from __future__ import annotations
from datetime import datetime
from base64 import urlsafe_b64encode, urlsafe_b64decode
import json
import uuid


def encode_cursor(ts: datetime, row_id: str | uuid.UUID) -> str:
    # Spara som JSON -> base64 så vi slipper delimiter-strul
    payload = {"ts": ts.isoformat(), "id": str(row_id)}
    raw = json.dumps(payload).encode("utf-8")
    return urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str | uuid.UUID]:
    # Lägg tillbaka ev. borttagna '=' för korrekt padding
    padding = "=" * (-len(cursor) % 4)
    data = urlsafe_b64decode((cursor + padding).encode("utf-8"))
    payload = json.loads(data.decode("utf-8"))

    ts = datetime.fromisoformat(payload["ts"])
    id_str = payload["id"]

    # Tolerant: försök parsas som UUID, annars behåll som str
    try:
        row_id = uuid.UUID(id_str)
    except Exception:
        row_id = id_str

    return ts, row_id
