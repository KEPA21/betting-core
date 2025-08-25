from fastapi.testclient import TestClient
from app.main import app


def test_missing_api_key_401():
    c = TestClient(app)
    r = c.get("/odds")
    assert r.status_code == 401
    body = r.json()
    assert body["code"] in ("unauthorized", "forbidden")


def test_reader_cannot_post_odds_403():
    c = TestClient(app)
    payload = {
        "items": [
            {
                "match_id": "m1",
                "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
                "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
                "price": 2.0,
                "captured_at": "2025-08-18T12:00:00Z",
            }
        ]
    }
    r = c.post("/odds", json=payload, headers={"X-API-Key": "reader1"})
    assert r.status_code in (401, 403)
