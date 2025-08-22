from __future__ import annotations
from uuid import uuid4
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

def get_request_id() -> str:
    return _request_id_ctx.get("-")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request_ID") or str(uuid4())
        request.state.request_id = rid
        token = _request_id_ctx.set(rid)
        try: 
            response = await call_next(request)
        finally:
            _request_id_ctx.reset(token)
        response.headers["X-Request-ID"] = rid
        return response