# app/core/security.py
from __future__ import annotations

import os
from typing import Optional, Iterable, Set, Dict, Any

from fastapi import Depends, Header, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

# ---- Konfig från env ----
AUTH_MODE = os.getenv("AUTH_MODE", "both").lower()  # "api_key" | "jwt" | "both"

JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_ISS = os.getenv("JWT_ISSUER", "betting-core")
JWT_AUD = os.getenv("JWT_AUDIENCE", "betting-clients")
JWT_SECRETS_RAW = os.getenv("JWT_SECRETS", "")  # ex: "v1:testsecret1,v2:testsecret2"
JWT_ACCEPTED_KIDS_RAW = os.getenv("JWT_ACCEPTED_KIDS", "")  # ex: "v1,v2"

HTTP_BEARER = HTTPBearer(auto_error=False)


def _parse_api_keys(s: str) -> Dict[str, Set[str]]:
    """
    API_KEYS: "writer1=read,odds:write;reader1=read"
    -> {"writer1": {"read","odds:write"}, "reader1":{"read"}}
    """
    out: Dict[str, Set[str]] = {}
    if not s:
        return out
    for part in s.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        key, scopes_str = part.split("=", 1)
        scopes = {x.strip() for x in scopes_str.split(",") if x.strip()}
        out[key.strip()] = scopes
    return out


def _parse_jwt_secrets(s: str) -> Dict[str, str]:
    """
    "v1:secret1,v2:secret2" -> {"v1":"secret1", "v2":"secret2"}
    """
    out: Dict[str, str] = {}
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            continue
        kid, secret = part.split(":", 1)
        out[kid.strip()] = secret.strip()
    return out


def _parse_kids(s: str) -> Set[str]:
    return {x.strip() for x in s.split(",") if x.strip()}


API_KEYS_MAP = _parse_api_keys(os.getenv("API_KEYS", ""))
JWT_SECRETS = _parse_jwt_secrets(JWT_SECRETS_RAW)
JWT_ACCEPTED_KIDS = _parse_kids(JWT_ACCEPTED_KIDS_RAW)


class Principal:
    def __init__(self, sub: str, scopes: Iterable[str]) -> None:
        self.sub = sub
        self.scopes = set(scopes)

    def has_scopes(self, required: Iterable[str]) -> bool:
        req = set(required)
        return req.issubset(self.scopes)


def _principal_from_apikey(x_api_key: Optional[str]) -> Optional[Principal]:
    if not x_api_key:
        return None
    scopes = API_KEYS_MAP.get(x_api_key)
    if not scopes:
        # okänd nyckel
        raise HTTPException(status_code=401, detail="invalid_api_key")
    return Principal(sub=x_api_key, scopes=scopes)


def _principal_from_jwt(
    auth: Optional[HTTPAuthorizationCredentials],
) -> Optional[Principal]:
    if not auth:
        return None
    token = auth.credentials
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token_header")

    kid = header.get("kid")
    if JWT_ACCEPTED_KIDS and (kid not in JWT_ACCEPTED_KIDS):
        raise HTTPException(status_code=401, detail="kid_not_accepted")

    key = None
    if kid:
        key = JWT_SECRETS.get(kid)
    # fallback: om bara en hemlighet finns och ingen kid, använd den
    if not key and len(JWT_SECRETS) == 1:
        key = next(iter(JWT_SECRETS.values()))

    if not key:
        raise HTTPException(status_code=401, detail="unknown_kid_or_no_key")

    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            key,
            algorithms=[JWT_ALG],
            audience=JWT_AUD,
            issuer=JWT_ISS,
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=401, detail=f"invalid_token: {e.__class__.__name__}"
        )

    scopes = payload.get("scopes")
    if scopes is None:
        # stöd för "scope": "read odds:write"
        scope_str = payload.get("scope")
        if isinstance(scope_str, str):
            scopes = scope_str.split()
        else:
            scopes = []
    elif isinstance(scopes, str):
        scopes = [scopes]

    sub = payload.get("sub") or "anonymous"
    return Principal(sub=sub, scopes=scopes)


async def get_principal(
    auth: Optional[HTTPAuthorizationCredentials] = Security(HTTP_BEARER),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> Principal:
    mode = AUTH_MODE
    # Om Authorization finns, försök JWT först
    if auth:
        p = _principal_from_jwt(auth)
        if p:
            return p
    # Annars försök API-nyckel
    if x_api_key:
        p = _principal_from_apikey(x_api_key)
        if p:
            return p

    # Inget hittades -> 401 med bra feltext
    if mode == "jwt":
        raise HTTPException(status_code=401, detail="missing_bearer_token")
    if mode == "api_key":
        raise HTTPException(status_code=401, detail="missing_api_key")
    # both
    raise HTTPException(status_code=401, detail="missing_credentials")


def require_scopes(*required: str):
    async def _dep(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_scopes(required):
            raise HTTPException(status_code=403, detail="insufficient_scope")
        return principal

    return _dep
