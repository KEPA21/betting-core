import time
import threading
from collections import deque
from typing import Deque, Dict
from fastapi import Request, HTTPException


class SimpleRateLimiter:
    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window = window_seconds
        self._lock = threading.Lock()
        self._bucket: Dict[str, Deque[float]] = {}

    def check(self, key: str):
        now = time.monotonic()
        with self._lock:
            dq = self._bucket.setdefault(key, deque())
            while dq and now - dq[0] > self.window:
                dq.popleft()
                if len(dq) >= self.max_events:
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
                dq.append(now)


# 200 requests / min per klient (PoC – ersätts av Redis i US12)
_odds_ingest_limiter = SimpleRateLimiter(200, 60)


async def limit_odds_ingest(request: Request):
    ip = (
        request.headers.get(
            "x-forwarded-for", (request.client.host if request.client else "unknown")
        )
        .split(",")[0]
        .strip()
    )
    _odds_ingest_limiter.check(ip)
