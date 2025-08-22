from __future__ import annotations
import os 
from typing import Callable, Dict, Set, List
from fastapi import HTTPException, status, Security, Request
from fastapi.security.api_key import APIKeyHeader
from app.core.settings import settings

def _parse_api_keys(raw: str | None) -> Dict[str, Set[str]]:
    if not raw:
        return {}
    out: Dict[str, Set[str]] = {}
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        if "=" not in entry:
            continue
        key, scopes = entry.split("=", 1)
        scope_set = {s.strip() for s in scopes.split(",") if s.strip()}
        out[key.strip()] = scope_set
    return out

_API_KEYS: Dict[str, Set[str]] = _parse_api_keys(settings.API_KEYS)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_scopes(*required: str) -> Callable:
    """
    Dependency som:
    - Läser X-API-Key
    - validerar key
    - kräver att ALLA 'required' scopes finns
    """
    required_set = set(required)

    def _dep(api_key: str | None = Security(api_key_header), request: Request = None):
        # Tillåt GET utan auth om ingen scope krävs (dvs. require_scopes() kallad utan args)
        if not required_set and api_key is None:
            return
        
        if api_key is None or api_key not in _API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        
        granted = _API_KEYS[api_key]
        if not required_set.issubset(granted):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scopes; required: {sorted(required_set)}, granted: {sorted(granted)}",
            )
        
        if request is not None:
            request.state.api_key = api_key
            request.state.scopes = granted
    
    return _dep