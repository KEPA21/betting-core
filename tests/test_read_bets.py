# tests/test_bets_read.py


def _post_bet(client, headers, *, match_id, user_ref, idem_key):
    payload = {
        "match_id": match_id,
        "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
        "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
        "stake": 123.45,
        "price": 1.85,
        "placed_at": "2025-01-01T12:00:00Z",
        "user_ref": user_ref,
        "idempotency_key": idem_key,
    }
    r = client.post("/bets", json=payload, headers=headers)
    assert r.status_code in (200, 201), r.text
    return r.json()["bet_id"]


def test_bets_get_list_and_filter_user_ref(client, writer_headers, reader_headers):
    # Skapa två bets med olika user_ref
    b1 = _post_bet(
        client,
        writer_headers,
        match_id="m_bets_list_1",
        user_ref="u1",
        idem_key="tbr-1",
    )
    b2 = _post_bet(
        client,
        writer_headers,
        match_id="m_bets_list_2",
        user_ref="u2",
        idem_key="tbr-2",
    )
    assert b1 and b2

    # Hämta alla
    r_all = client.get("/bets?limit=50", headers=reader_headers)
    assert r_all.status_code == 200, r_all.text
