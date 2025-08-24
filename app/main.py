import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from opentelemetry import trace
from app.core.request_id import RequestIdMiddleware
from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    integrity_exception_handler,
    request_validation_exception_handler,
)
from app.routers.health import router as health_router
from app.routers.readiness import router as readiness_router
from app.routers.odds import router as odds_router
from app.routers.predictions import router as predictions_router
from app.routers.bets import router as bets_router
from app.observability.metrics import metrics_router, MetricsMiddleware
from app.observability.logging import setup_logging
from app.observability.request_log import RequestLoggingMiddleware
from app.observability.tracing import setup_tracing
from app.observability.trace_filter import TraceContextFilter
from app.core.db import engine

load_dotenv()

if os.getenv("JSON_LOGS", "1") == "1":
    from app.core.logging import configure_json_logging

    configure_json_logging()

setup_logging()
logging.getLogger().addFilter(TraceContextFilter())
logging.getLogger("uvicorn.access").addFilter(TraceContextFilter())

tags_metadata = [
    {"name": "system", "description": "Hälso- & readiness-endpoints"},
    {"name": "odds", "description": "Ingest & läsning av odds (bulk upsert)"},
    {"name": "predictions", "description": "Modellprediktioner per match och version"},
    {"name": "bets", "description": "Registrering och läsning av bets (idempotent)"},
]

app = FastAPI(
    title="100kbetting – Core API",
    version="0.1.0",
    description="Ingest och exponering av odds, predictions och bets.",
    openapi_tags=tags_metadata,
    contact={"name": "100kbetting", "url": "https://example.com"},
    license_info={"name": "Proprietary"},
)

setup_tracing(app, engine)

# Request-ID
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(MetricsMiddleware)

# Standardiserade gel
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)


@app.get("/_auth_example", include_in_schema=False)
def _auth_example():
    return {"hint": "Send X-API-KEY: <your_key> in headers"}


# Test-only endpoint för att trigga unhandled exception
if os.getenv("ENABLE_TEST_ENDPOINTS", "1") == "1":

    @app.get("/_boom", include_in_schema=False, tags=["system"])
    def _boom():
        raise RuntimeError("kaboom")


@app.middleware("http")
async def add_trace_headers(request, call_next):
    resp = await call_next(request)
    sc = trace.get_current_span().get_span_context()
    if sc and sc.is_valid:
        resp.headers["trace-id"] = format(sc.trace_id, "032x")
        resp.headers["span-id"] = format(sc.span_id, "016x")
        # Alternativ enligt W3C:
        # resp.headers["traceparent"] = f"00-{format(sc.trace_id,'032x')}-{format(sc.span_id,'016x')}-01"
    return resp


app.include_router(health_router, tags=["system"])
app.include_router(readiness_router, tags=["system"])
app.include_router(odds_router, tags=["odds"])
app.include_router(predictions_router, tags=["predictions"])
app.include_router(bets_router, tags=["bets"])
app.include_router(metrics_router, tags=["observability"])
