import base64
from uuid import UUID
from datetime import datetime, timezone


def encode_cursor(ts: datetime, id_: UUID) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    raw = f"{ts.isoformat()}|{id_}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    padding = "=" * (-len(cursor) % 4)
    raw = base64.urlsafe_b64decode((cursor + padding).encode()).decode()
    ts_str, id_str = raw.split("|", 1)
    return (datetime.fromisoformat(ts_str), UUID(id_str))
