def test_odds_invalid_cursor_400_again(client, reader_headers):
    r = client.get("/odds?cursor=NOT_BASE64", headers=reader_headers)
    assert r.status_code == 400
