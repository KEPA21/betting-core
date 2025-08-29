from datetime import datetime, timezone
from sqlalchemy import text
from app.core.db import engine

BOOKMAKER_ID = "024c6a47-1a14-4549-935f-31e22e747670"
SELECTION_ID = "bea8671c-e889-4e3d-91d3-b407bc186408"


def _post_bet(client, headers, **overrides):
    payload = {
        "match_id": "m_list_case",
        "bookmaker_id": BOOKMAKER_ID,
        "selection_id": SELECTION_ID,
        "stake": 50.0,
        "price": 1.90,
        "placed_at": "2025-01-01T12:00:00Z",
        "user_ref": "u_list_tests",
        "idempotency_key": f"k-{datetime.now(timezone.utc).timestamp()}",
    }
    payload.update(overrides)
    r = client.post("/bets", json=payload, headers=headers)
    # tolerant (idempotent re-runs): accept 200 or 201
    assert r.status_code in (200, 201)
    return r.json(), payload


def test_bets_list_no_filter_has_shape(client, writer_headers, reader_headers):
    # create at least one bet to ensure non-empty
    _post_bet(client, writer_headers)

    r = client.get("/bets", headers=reader_headers)
    assert r.status_code == 200
    body = r.json()
    # shape
    assert "items" in body and "total" in body
    assert isinstance(body["items"], list)
    # items contain expected fields
    if body["items"]:
        item = body["items"][0]
        for key in (
            "bet_id",
            "match_id",
            "bookmaker_id",
            "selection_id",
            "stake",
            "price",
            "placed_at",
            "status",
        ):
            assert key in item


def test_bets_filter_user_ref_and_status(client, writer_headers, reader_headers):
    # two bets for same user_ref
    b1, p1 = _post_bet(
        client, writer_headers, user_ref="u_filter", idempotency_key="k-filter-1"
    )
    b2, p2 = _post_bet(
        client, writer_headers, user_ref="u_filter", idempotency_key="k-filter-2"
    )

    # flip one to "won" directly (keeps the test API-only except this line)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE core.bets SET status='won' WHERE idempotency_key=:k"),
            {"k": "k-filter-2"},
        )

    # Note: if your query param is named `bet_status` without alias, use `?bet_status=open` instead
    r = client.get("/bets?user_ref=u_filter&status=open", headers=reader_headers)
    assert r.status_code == 200
    items = r.json()["items"]
    keys = {it["idempotency_key"] for it in items}
    # open one should be present, won one should be filtered out
    assert "k-filter-1" in keys
    assert "k-filter-2" not in keys


def test_bets_pagination_next_offset(client, writer_headers, reader_headers):
    # create 3 bets for a dedicated user to isolate
    _post_bet(client, writer_headers, user_ref="u_paging", idempotency_key="k-page-1")
    _post_bet(client, writer_headers, user_ref="u_paging", idempotency_key="k-page-2")
    _post_bet(client, writer_headers, user_ref="u_paging", idempotency_key="k-page-3")

    r = client.get("/bets?user_ref=u_paging&limit=1&offset=1", headers=reader_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1
    # total >= 3 and next_offset should be 2 when limit=1, offset=1, total>=3
    assert body["total"] >= 3
    assert body["next_offset"] == 2
