def test_odds_post_validation_422(client, writer_headers):
    # Skickar en ogiltig payload (saknar "items")
    r = client.post("/odds", json={}, headers=writer_headers)
    assert r.status_code == 422
    body = r.json()
    # Standardiserat felobjekt: minst dessa nycklar ska finnas
    assert "code" in body and "message" in body and "traceId" in body


def test_odds_invalid_cursor_400(client, reader_headers):
    # Ogiltig cursor triggar 400 bad_request
    r = client.get("/odds?cursor=NOT_BASE64", headers=reader_headers)
    assert r.status_code == 400
    body = r.json()
    assert body["code"] == "bad_request"
