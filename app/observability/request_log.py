import time, json, logging
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger("access")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = None
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            latency_ms = int((time.time() - start) * 1000)
            rid = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "level": "INFO",
                "logger": "access",
                "msg": "request",
                "request_id": rid,
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "latency_ms": latency_ms,
            }
            log.info(json.dumps(entry))
