def test_readyz_happy_path(client):
    r = client.get("/readyz")
    # I din miljö finns readiness-view: förväntar 200 med counts
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ready"
    assert "counts" in j and "markets" in j["counts"]


def test_odds_invalid_cursor_400(client, reader_headers):
    r = client.get("/odds?cursor=not-a-valid-cursor", headers=reader_headers)
    assert r.status_code == 400
    j = r.json()
    # Din handler mappar 400 → {"code":"bad_request", ...}
    assert j["code"] in (
        "bad_request",
        "invalid_request",
        "badrequest",
        "bad_request",
    )  # tolerant
    assert "invalid cursor" in j["message"].lower()


def test_unhandled_exception_500(client):
    r = client.get("/_boom")
    assert r.status_code == 500
    j = r.json()
    assert j["code"] == "internal_error"
    assert "traceId" in j


def test_requires_api_key_401(client):
    r = client.get("/odds?match_id=m1")
    assert r.status_code == 401
