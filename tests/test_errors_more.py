# tests/test_errors_more.py
import json
import asyncio
from starlette.requests import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from psycopg.errors import ForeignKeyViolation, UniqueViolation, CheckViolation

from app.core.errors import (
    integrity_exception_handler,
    request_validation_exception_handler,
)


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _req(path="/x"):
    scope = {"type": "http", "method": "GET", "path": path, "headers": []}
    req = Request(scope)
    req.state.request_id = "req-xyz"
    return req


def _diag(table: str, constraint: str):
    return type("Diag", (), {"constraint_name": constraint, "table_name": table})()


class MyFK(ForeignKeyViolation):
    def __init__(self):
        self._d = _diag("bets", "fk_sel")
        super().__init__("fk violation")

    @property
    def diag(self):
        return self._d


class MyUQ(UniqueViolation):
    def __init__(self):
        self._d = _diag("odds", "uq_odds")
        super().__init__("unique violation")

    @property
    def diag(self):
        return self._d


class MyCK(CheckViolation):
    def __init__(self):
        self._d = _diag("odds", "ck_price")
        super().__init__("check violation")

    @property
    def diag(self):
        return self._d


def test_integrity_handler_fk_404():
    exc = IntegrityError("stmt", {}, MyFK())
    resp = _run(integrity_exception_handler(_req("/bets"), exc))
    body = json.loads(resp.body)
    assert resp.status_code == 404
    assert body["code"] == "not_found"
    assert "foreign key" in body["message"].lower()


def test_integrity_handler_unique_409():
    exc = IntegrityError("stmt", {}, MyUQ())
    resp = _run(integrity_exception_handler(_req("/odds"), exc))
    body = json.loads(resp.body)
    assert resp.status_code == 409
    assert body["code"] == "conflict"


def test_integrity_handler_check_400():
    exc = IntegrityError("stmt", {}, MyCK())
    resp = _run(integrity_exception_handler(_req("/odds"), exc))
    body = json.loads(resp.body)
    assert resp.status_code == 400
    assert body["code"] == "bad_request"


def test_integrity_handler_fallback_500():
    exc = IntegrityError("stmt", {}, Exception("weird"))
    resp = _run(integrity_exception_handler(_req("/x"), exc))
    body = json.loads(resp.body)
    assert resp.status_code == 500
    assert body["code"] == "internal_error"


def test_request_validation_handler_shapes_422():
    err_list = [
        {"loc": ("body", "items", 0, "match_id"), "msg": "field required"},
        {"loc": ("query", "limit"), "msg": "value is not a valid integer"},
    ]
    exc = RequestValidationError(err_list)
    resp = _run(request_validation_exception_handler(_req("/odds"), exc))
    body = json.loads(resp.body)
    assert resp.status_code == 422
    assert body["code"] == "validation_error"
    fields = {fe["field"] for fe in body["fieldErrors"]}
    assert "items.0.match_id" in fields
    assert "query.limit" in fields
