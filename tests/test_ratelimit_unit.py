from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.core.ratelimit import rate_limit_dependency, noop_dependency


class FakeRedis:
    async def script_load(self, _lua):
        return "sha"

    async def time(self):
        return (1_000, 0)

    async def evalsha(self, *_args):
        return [0, 0.0, 3, 5]

    async def eval(self, *_args):
        return [0, 0.0, 3, 5]


def build_app_with(dep):
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(dep)])
    def ping():
        return {"ok": True}

    return app


def test_rate_limit_429(monkeypatch):
    import app.core.ratelimit as rl

    monkeypatch.setattr(rl, "get_redis", lambda: FakeRedis())

    dep = rate_limit_dependency("test_bucket", capacity=1, refill_per_sec=1.0)
    app = build_app_with(dep)
    c = TestClient(app)

    r = c.get("/ping", headers={"X-API-Key": "writer1"})
    assert r.status_code == 429
    assert r.headers.get("Retry-After") is not None
    assert r.headers.get("X-RateLimit-Limit") == "1"
    assert r.headers.get("X-RateLimit-Remaining") == "0"
    assert r.headers.get("X-RateLimit-Reset") is not None


def test_rate_limit_noop_allows():
    app = build_app_with(noop_dependency)
    c = TestClient(app)
    r = c.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
