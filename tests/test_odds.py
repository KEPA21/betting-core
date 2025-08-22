from datetime import datetime, timezone
import uuid

MATCH_ID = "m1"
BOOKMAKER_ID = "024c6a47-1a14-4549-935f-31e22e747670"
SELECTION_ID = "bea8671c-e889-4e3d-91d3-b407bc186408"

def test_get_odds_requires_auth(client):
    r = client.get("/odds", params={"match_id": MATCH_ID})
    assert r.status_code == 401
    body = r.json()
    assert body["code"] == "unauthorized"

def test_post_odds_reader_forbidden(client, reader_headers):
    payload = {
        "items": [
            {
                "match_id": MATCH_ID,
                "bookmaker_id": BOOKMAKER_ID,
                "selection_id": SELECTION_ID,
                "price": 2.0,
                "captured_at": "2030-01-01T00:00:00Z",
            }
        ]
    }
    r = client.post("/odds", headers=reader_headers, json=payload)
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == "forbidden"

def test_post_odds_validation_422(client, writer_headers):
    payload = {
        "items": [
            {
                "match_id": MATCH_ID,
                "bookmaker_id": BOOKMAKER_ID,
                "selection_id": SELECTION_ID,
                "price": "NaN",
                "captured_at": "2030-01-01T00:00:00Z",
            }
        ]
    }
    r = client.post("/odds", headers=writer_headers, json=payload)
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validation_error"
    assert body["traceId"]
 
def test_post_odds_fk_404(client, writer_headers):
    payload = {
        "items": [
            {
                "match_id": "m404",
                "bookmaker_id": str(uuid.UUID(int=0)),
                "selection_id": str(uuid.UUID(int=0)),
                "price": 2.0,
                "captured_at": "2030-01-02T00:00:00Z",
            }
        ]
    }
    r = client.post("/odds", headers=writer_headers, json=payload)
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == "not_found"
    assert "unknown bookmaker_id" in body["message"] or "unknown selection_id" in body["message"]

def test_post_odds_upsert_and_cursor_paging(client, writer_headers, reader_headers):
    captured_at = datetime(2030, 1, 3, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    # 1) upsert OK
    payload = {
        "items": [
            {
                "match_id": MATCH_ID,
                "bookmaker_id": BOOKMAKER_ID,
                "selection_id": SELECTION_ID,
                "price": 2.22,
                "probability": 0.45,
                "captured_at": captured_at,
                "source": "test",
            }
        ]
    }

    r = client.post("/odds", headers=writer_headers, json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["inserted"] + body["updated"] == 1

    # 2) GET med limit=1 ska returnera items + next_cursor
    r = client.get("/odds", headers=reader_headers, params={"match_id": MATCH_ID, "limit": 1})
    assert r.status_code == 200
    page1 = r.json()
    assert "items" in page1 and "total" in page1
    assert page1.get("next_cursor") is not None or page1.get("next_offset") is not None

    # 3) Om cursor finns, hämta nästa sida via cursor
    if page1.get("next_cursor"):
        r2 = client.get(
            "/odds",
            headers=reader_headers,
            params={"match_id": MATCH_ID, "limit": 1, "cursor": page1["next_cursor"]}
        )
        assert r2.status_code == 200
        page2 = r2.json()
        assert "items" in page2
    else:
        r2 = client.get(
            "/odds",
            headers= reader_headers,
            params={"match_id": MATCH_ID, "limit": 1, "offset": page1["next_offset"]}
        )
        assert r2.status_code == 200
        page2 = r2.json()
        assert "items" in page2
        


