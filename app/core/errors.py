from __future__ import annotations
import logging
from typing import List
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from psycopg.errors import ForeignKeyViolation, UniqueViolation, CheckViolation, NotNullViolation

from app.schemas.errors import ErrorResponse, FieldError
from app.core.request_id import get_request_id

log = logging.getLogger("app.errors")

# def _loc_to_field(loc: List[object]) -> str:
#     parts = [str(x) for x in loc if x != "body"]
#     return ".".join(parts) if parts else ""

# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     trace_id = getattr(request.state, "request_id", get_request_id())
#     field_errors = [FieldError(field=_loc_to_field(err["loc"]), message=err["msg"]) for err in exc.errors()]
#     payload = ErrorResponse(code="validation error", message="Validation failed", fieldErrors=field_errors, traceId=trace_id).model_dump()
#     log.info("422 validation_error traceId=%s errors=%d path=%s", trace_id, len(field_errors), request.url.path)
#     return JSONResponse(status_code=422, content=payload)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, "request_id", get_request_id())
    code_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        429: "rate_limited",
    }
    code = code_map.get(exc.status_code, f"http_{exc.status_code}")
    msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    payload = ErrorResponse(code=code, message=msg, traceId=trace_id).model_dump()
    log.warning("%d %s traceId=%s path=%s", exc.status_code, code, trace_id, request.url.path)
    return JSONResponse(status_code=exc.status_code, content=payload)

async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "request_id", get_request_id())
    log.exception("500 internal_error traceId=%s path=%s", trace_id, request.url.path)
    payload = ErrorResponse(code="internal_error", message="An unexpected error occurred", traceId=trace_id).model_dump()
    return JSONResponse(status_code=500, content=payload)

async def integrity_exception_handler(request: Request, exc: IntegrityError):
    trace_id = getattr(request.state, "request_id", get_request_id())
    orig = getattr(exc, "orig", None)
    # Försök plocka ut lite diagnostik från psycopg
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    table = getattr(diag, "table_name", None)

    def _msg(base: str) -> str:
        extras = []
        if table:
            extras.append(f"table={table}")
        if constraint:
            extras.append(f"constraint={constraint}")
        return f"{base} ({', '.join(extras)})" if extras else base

    # FK bryts -> 404
    if isinstance(orig, ForeignKeyViolation):
        payload = ErrorResponse(code="not_found", message=_msg("Related resource not found (foreign key)"), traceId=trace_id).model_dump()
        log.warning("404 fk_violation traceId=%s path=%s %s", trace_id, request.url.path, payload["message"])
        return JSONResponse(status_code=404, content=payload)

    # Uniknyckel krock -> 409
    if isinstance(orig, UniqueViolation):
        payload = ErrorResponse(code="conflict", message=_msg("Unique constraint violated"), traceId=trace_id).model_dump()
        log.warning("409 unique_violation traceId=%s path=%s %s", trace_id, request.url.path, payload["message"])
        return JSONResponse(status_code=409, content=payload)

    # CHECK/NOT NULL m.m. -> 400 (bad request)
    if isinstance(orig, (CheckViolation, NotNullViolation)):
        payload = ErrorResponse(code="bad_request", message=_msg("Constraint violated"), traceId=trace_id).model_dump()
        log.warning("400 constraint_violation traceId=%s path=%s %s", trace_id, request.url.path, payload["message"])
        return JSONResponse(status_code=400, content=payload)

    # Fallback
    log.exception("500 integrity_error traceId=%s path=%s", trace_id, request.url.path)
    payload = ErrorResponse(code="internal_error", message="Database integrity error", traceId=trace_id).model_dump()
    return JSONResponse(status_code=500, content=payload)

async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "request_id", get_request_id())
    field_errors = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body") or "body"
        field_errors.append({"field": loc, "message": err.get("msg")})
    payload = ErrorResponse(
        code="validation_error",
        message="Validation failed",
        fieldErrors=field_errors,
        traceId=trace_id
    ).model_dump()
    return JSONResponse(status_code=422, content=payload)

