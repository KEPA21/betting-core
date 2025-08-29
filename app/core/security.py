# app/core/security.py
from __future__ import annotations
import os
from typing import Optional, Set, Dict, Tuple
from fastapi import Depends, Header, HTTPException, Request
import jwt  # PyJWT


def _env() -> dict:
    return {
        "auth_mode": os.getenv("AUTH_MODE", "both").lower(),
        "api_keys": os.getenv("API_KEYS", ""),
        "jwt_alg": os.getenv("JWT_ALG", "HS256"),
        "jwt_iss": os.getenv("JWT_ISSUER"),
        "jwt_aud": os.getenv("JWT_AUDIENCE"),
        # rotation (enkelt)
        "jwt_secret": os.getenv("JWT_SECRET"),
        "jwt_prev": os.getenv("JWT_PREVIOUS_SECRET"),
        # KID-ring
        "jwt_secrets": os.getenv("JWT_SECRETS", ""),  # "v1:sec1,v2:sec2"
        "jwt_accepted_kids": os.getenv("JWT_ACCEPTED_KIDS", ""),  # "v1,v2"
    }


def _parse_api_keys(s: str) -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    if not s:
        return out
    for part in filter(None, (p.strip() for p in s.split(";"))):
        if "=" not in part:
            continue
        key, scopes_str = part.split("=", 1)
        scopes = {x for x in scopes_str.replace(",", " ").split() if x}
        out[key.strip()] = scopes
    return out


def _parse_kid_secrets(s: str) -> Dict[str, str]:
    # "v1:sec1,v2:sec2"
    out: Dict[str, str] = {}
    if not s:
        return out
    for part in filter(None, (p.strip() for p in s.split(","))):
        if ":" not in part:
            continue
        kid, sec = part.split(":", 1)
        out[kid.strip()] = sec.strip()
    return out


def _parse_csv_set(s: str) -> Set[str]:
    return {x for x in s.replace(",", " ").split() if x}


def _normalize_scopes(val) -> Set[str]:
    if isinstance(val, str):
        return {x for x in val.replace(",", " ").split() if x}
    if isinstance(val, (list, tuple, set)):
        return {str(x) for x in val if str(x)}
    return set()


def _decode_with_kid(token: str, env: dict) -> Tuple[Set[str], dict]:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    kid_map = _parse_kid_secrets(env["jwt_secrets"])
    if not kid or kid not in kid_map:
        raise HTTPException(status_code=401, detail="invalid token (kid)")
    accepted = _parse_csv_set(env["jwt_accepted_kids"])
    if accepted and kid not in accepted:
        raise HTTPException(status_code=401, detail="kid not accepted")
    secret = kid_map[kid]
    kwargs = {"algorithms": [env["jwt_alg"]]}
    if env["jwt_iss"]:
        kwargs["issuer"] = env["jwt_iss"]
    if env["jwt_aud"]:
        kwargs["audience"] = env["jwt_aud"]
    payload = jwt.decode(token, secret, **kwargs)
    scopes = _normalize_scopes(payload.get("scopes"))
    return scopes, payload


def _decode_with_rotation(token: str, env: dict) -> Tuple[Set[str], dict]:
    secrets = [env["jwt_secret"], env["jwt_prev"]]
    last_err: Optional[Exception] = None
    for sec in secrets:
        if not sec:
            continue
        try:
            kwargs = {"algorithms": [env["jwt_alg"]]}
            if env["jwt_iss"]:
                kwargs["issuer"] = env["jwt_iss"]
            if env["jwt_aud"]:
                kwargs["audience"] = env["jwt_aud"]
            payload = jwt.decode(token, sec, **kwargs)
            scopes = _normalize_scopes(payload.get("scopes"))
            return scopes, payload
        except Exception as e:
            last_err = e
            continue
    raise last_err or HTTPException(status_code=401, detail="invalid token")


async def auth_dependency(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, convert_underscores=False),
    authorization: Optional[str] = Header(default=None),
):
    env = _env()

    def want_api_key() -> bool:
        return env["auth_mode"] in ("api_key", "both")

    def want_jwt() -> bool:
        return env["auth_mode"] in ("jwt", "both")

    # API key path
    if want_api_key() and x_api_key:
        scopes = _parse_api_keys(env["api_keys"]).get(x_api_key)
        if scopes is None:
            raise HTTPException(status_code=401, detail="invalid api key")
        return {"principal": f"apikey:{x_api_key}", "scopes": scopes}

    # JWT path
    if want_jwt() and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            # Först: om KID-ring finns => använd den
            if env["jwt_secrets"]:
                scopes, payload = _decode_with_kid(token, env)
            else:
                scopes, payload = _decode_with_rotation(token, env)
            sub = str(payload.get("sub", "unknown"))
            return {"principal": f"jwt:{sub}", "scopes": scopes}
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="token expired")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="invalid token")

    raise HTTPException(status_code=401, detail="missing credentials")


def require_scopes(*required: str):
    needed = set()
    for r in required:
        needed.update(_normalize_scopes(r))

    async def _dep(auth=Depends(auth_dependency)):
        have = set(auth.get("scopes", set()))
        if not needed.issubset(have):
            raise HTTPException(status_code=403, detail="insufficient_scope")
        return auth

    return _dep
