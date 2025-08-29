from uuid import uuid4


def test_bets_idempotency(client, writer_headers):
    payload = {
        "match_id": "m1",
        "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
        "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
        "stake": 100.0,
        "price": 1.85,
        "placed_at": "2025-01-01T12:00:00Z",
        "idempotency_key": f"demo-{uuid4()}",
    }

    # Första gången -> 201 Created
    r1 = client.post("/bets", json=payload, headers=writer_headers)
    assert r1.status_code == 201
    b1 = r1.json()
    assert b1["created"] is True
    assert b1["bet_id"]

    # Samma payload/nyckel igen -> 200 och samma bet_id
    r2 = client.post("/bets", json=payload, headers=writer_headers)
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2["created"] is False
    assert b2["bet_id"] == b1["bet_id"]
    assert r2.headers.get("x-idempotent-replayed") == "true"
