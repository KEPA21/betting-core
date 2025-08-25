from datetime import datetime, timezone
from app.core.pagination import encode_cursor, decode_cursor


def test_cursor_roundtrip():
    ts = datetime(2025, 1, 1, 12, 34, 56, tzinfo=timezone.utc)
    cur = encode_cursor(ts, "abc-123")
    ts2, id2 = decode_cursor(cur)
    assert ts2 == ts
    assert id2 == "abc-123"
