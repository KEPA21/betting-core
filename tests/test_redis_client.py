from app.core.redis_client import get_redis


def test_get_redis_does_not_connect(monkeypatch):
    # Skapa klientobjekt (init) – ska inte kräva att Redis körs
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    r = get_redis()
    assert r is not None
