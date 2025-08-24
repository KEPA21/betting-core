def test_predictions_get_reader_ok(client, reader_headers):
    r = client.get("/predictions?match_id=m1&limit=1", headers=reader_headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    if body["items"] and body.get("next_cursor"):
        r2 = client.get(
            f"/predictions?match_id=m1&limit=1&cursor={body['next_cursor']}",
            headers=reader_headers,
        )
        assert r2.status_code == 200


def test_predictions_post_422_validation_error(client, writer_headers):
    # Saknar obligatoriska fält -> 422 från din validation handler
    r = client.post(
        "/predictions", headers=writer_headers, json={"items": [{"match_id": "m1"}]}
    )
    assert r.status_code == 422
    j = r.json()
    assert j["code"] == "validation_error"


def test_predictions_post_404_unknown_fk(client, writer_headers):
    bad = {
        "items": [
            {
                "match_id": "m1",
                "model_id": "00000000-0000-0000-0000-000000000000",
                "version": "1.0",
                "selection_id": "00000000-0000-0000-0000-000000000000",
                "probability": 0.5,
                "odds_fair": 2.0,
                "features": {},
                "predicted_at": "2025-08-18T12:00:00Z",
            }
        ]
    }
    r = client.post("/predictions", headers=writer_headers, json=bad)
    assert r.status_code == 404
    # Din 404-format: {"code":"not_found","message":"unknown ..."}
    j = r.json()
    assert j["code"] == "not_found"
    assert "unknown" in j["message"]
