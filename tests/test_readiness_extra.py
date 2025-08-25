def test_readyz_db_down_returns_503(client, monkeypatch):
    # Patcha symbolen där den används (importerad i readiness-modulen)
    def _raise():
        raise Exception("db down")

    monkeypatch.setattr("app.routers.readiness.ping_db", _raise, raising=True)

    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["code"] in ("service_unavailable", "internal_error")


def test_readyz_view_missing_returns_503(client, monkeypatch):
    # Fejka engine.connect() så att readiness-vyn ser "tomt"
    class FakeConn:
        def execute(self, *_args, **_kwargs):
            class R:
                def first(self):
                    return None

            return R()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class FakeEngineCtx:
        def __enter__(self):
            return FakeConn()

        def __exit__(self, *a):
            return False

    # Patcha rätt symboler i readiness-modulen
    monkeypatch.setattr(
        "app.routers.readiness.engine.connect", lambda: FakeEngineCtx(), raising=True
    )
    monkeypatch.setattr("app.routers.readiness.ping_db", lambda: None, raising=True)

    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert "readiness" in body["message"].lower()
