import asyncio
from fastapi import HTTPException, Request
from starlette.responses import Response
from starlette.datastructures import Headers
from app.core.redis_client import get_redis
from app.core.ratelimit import _headers
from app.core.errors import http_exception_handler, unhandled_exception_handler


def _fake_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/_test",
        "headers": Headers({}).raw,
    }
    # create a Request; receive kan vara None i test
    req = Request(scope, receive=None)
    # sätt bara ett attribut på state (inte ersätta state-objektet)
    req.state.request_id = "req-123"
    return req


def test_redis_client_singleton():
    r1 = get_redis()
    r2 = get_redis()
    assert r1 is r2


def test_ratelimit_headers_helper_sets_headers():
    resp = Response()
    _headers(resp, limit=10, remaining=7, reset=3)
    assert resp.headers["X-RateLimit-Limit"] == "10"
    assert resp.headers["X-RateLimit-Remaining"] == "7"
    assert resp.headers["X-RateLimit-Reset"] == "3"


def test_ratelimit_headers_nonnegative():
    resp = Response()
    _headers(resp, limit=5, remaining=-1, reset=-3)
    assert resp.headers["X-RateLimit-Remaining"] == "0"
    assert resp.headers["X-RateLimit-Reset"] == "0"


def test_http_exception_handler_uses_detail_dict_when_present():
    req = _fake_request()
    exc = HTTPException(
        status_code=503,
        detail={"code": "service_unavailable", "message": "readiness down"},
    )
    resp = asyncio.run(http_exception_handler(req, exc))
    assert resp.status_code == 503
    body = resp.body.decode()
    assert '"service_unavailable"' in body
    assert '"readiness down"' in body
    assert '"traceId":"req-123"' in body


def test_http_exception_handler_builds_from_string_detail():
    req = _fake_request()
    exc = HTTPException(status_code=404, detail="nope")
    resp = asyncio.run(http_exception_handler(req, exc))
    assert resp.status_code == 404
    body = resp.body.decode()
    assert '"not_found"' in body
    assert '"nope"' in body


def test_unhandled_exception_handler_shapes_500():
    req = _fake_request()
    exc = RuntimeError("boom")
    resp = asyncio.run(unhandled_exception_handler(req, exc))
    assert resp.status_code == 500
    body = resp.body.decode()
    assert '"internal_error"' in body
    assert '"traceId":"req-123"' in body
