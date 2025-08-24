from __future__ import annotations

import json
from typing import List
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

WRITER = {"X-API-Key": "writer1", "content-type": "application/json"}
READER = {"X-API-Key": "reader1"}

# Befintliga seedade UUID:er i din DB/migrations
BOOKMAKER_ID = "024c6a47-1a14-4549-935f-31e22e747670"
SELECTION_ID = "bea8671c-e889-4e3d-91d3-b407bc186408"
MODEL_ID = "5c53bd4d-088d-48ca-8530-6d517a6597f9"


def _post_odds_batch(match_id: str, stamps: List[str]) -> None:
    """
    Skapar odds för en match vid givna timestamps (captured_at).
    """
    items = [
        {
            "match_id": match_id,
            "bookmaker_id": BOOKMAKER_ID,
            "selection_id": SELECTION_ID,
            "price": 2.0 + i * 0.01,
            "probability": 0.5,
            "captured_at": ts,
            "source": "cursor-test",
        }
        for i, ts in enumerate(stamps)
    ]
    r = client.post("/odds", headers=WRITER, data=json.dumps({"items": items}))
    assert r.status_code == 200, r.text


def _post_predictions_batch(match_id: str, stamps: List[str]) -> None:
    """
    Skapar predictions för en match vid givna timestamps (predicted_at).
    """
    items = [
        {
            "match_id": match_id,
            "model_id": MODEL_ID,
            "version": "cursor-1",
            "selection_id": SELECTION_ID,
            "probability": 0.55 + (i * 0.01),
            "odds_fair": 1.80,
            "features": {"i": i},
            "predicted_at": ts,
        }
        for i, ts in enumerate(stamps)
    ]
    r = client.post("/predictions", headers=WRITER, data=json.dumps({"items": items}))
    assert r.status_code == 200, r.text


def _fetch_page_odds(
    match_id: str, limit: int, cursor: str | None = None, offset: int | None = None
):
    params = {"match_id": match_id, "limit": str(limit)}
    if cursor is not None:
        params["cursor"] = cursor
    if offset is not None:
        params["offset"] = str(offset)
    r = client.get("/odds", headers=READER, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def _fetch_page_predictions(
    match_id: str, limit: int, cursor: str | None = None, offset: int | None = None
):
    params = {"match_id": match_id, "limit": str(limit)}
    if cursor is not None:
        params["cursor"] = cursor
    if offset is not None:
        params["offset"] = str(offset)
    r = client.get("/predictions", headers=READER, params=params)
    assert r.status_code == 200, r.text
    return r.json()


def test_odds_cursor_pagination():
    match = "m_cursor_odds_1"
    # Skapa 4 datapunkter i stigande tid
    stamps = [
        "2025-01-01T12:00:00Z",
        "2025-01-01T12:01:00Z",
        "2025-01-01T12:02:00Z",
        "2025-01-01T12:03:00Z",
    ]
    _post_odds_batch(match, stamps)

    # Page 1 (utan cursor) -> borde ge 2 items, next_cursor och next_offset=2
    page1 = _fetch_page_odds(match_id=match, limit=2)
    items1 = page1["items"]
    assert len(items1) == 2
    assert page1["total"] >= 4  # minst våra 4
    assert page1["next_cursor"] is not None
    assert page1["next_offset"] == 2

    # Page 2 (med cursor från page1)
    cur = page1["next_cursor"]
    page2 = _fetch_page_odds(match_id=match, limit=2, cursor=cur)
    items2 = page2["items"]
    assert len(items2) == 2
    # vid cursor-paging lämnas next_offset som None
    assert page2["next_offset"] is None

    # Kombinera och säkerställ att vi inte har dubletter och att ordningen följer timestamps
    ids = [it["odds_id"] for it in (items1 + items2)]
    assert len(ids) == len(set(ids)) == 4

    times = [it["captured_at"] for it in (items1 + items2)]
    assert times == sorted(times)  # stigande tidsordning


def test_predictions_cursor_pagination():
    match = "m_cursor_preds_1"
    stamps = [
        "2025-02-02T10:00:00Z",
        "2025-02-02T10:00:05Z",
        "2025-02-02T10:00:10Z",
        "2025-02-02T10:00:15Z",
    ]
    _post_predictions_batch(match, stamps)

    # Page 1
    page1 = _fetch_page_predictions(match_id=match, limit=2)
    items1 = page1["items"]
    assert len(items1) == 2
    assert page1["total"] >= 4
    assert page1["next_cursor"] is not None
    assert page1["next_offset"] == 2

    # Page 2 (cursor)
    cur = page1["next_cursor"]
    page2 = _fetch_page_predictions(match_id=match, limit=2, cursor=cur)
    items2 = page2["items"]
    assert len(items2) == 2
    assert page2["next_offset"] is None

    # Inga dubbletter, stigande predicted_at
    ids = [it["prediction_id"] for it in (items1 + items2)]
    assert len(ids) == len(set(ids)) == 4

    times = [it["predicted_at"] for it in (items1 + items2)]
    assert times == sorted(times)
