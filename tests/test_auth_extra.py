def test_forbidden_on_odds_post_with_reader(client, reader_headers):
    r = client.post("/odds", json={}, headers=reader_headers)
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == "forbidden"
