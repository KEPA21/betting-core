import os
import sys
import jwt
import datetime as dt
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# --- Lägg repo-roten på sys.path ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("AUTH_MODE", "both")
os.environ.setdefault("JWT_ALG", "HS256")
os.environ.setdefault("JWT_ISSUER", "betting-core")
os.environ.setdefault("JWT_AUDIENCE", "betting-clients")
os.environ.setdefault("JWT_SECRETS", "v1:testsecret1,v2:testsecret2")
os.environ.setdefault("JWT_ACCEPTED_KIDS", "v1,v2")

# --- Sätt test-vänliga envs INNAN appen importeras ---
os.environ.setdefault(
    "API_KEYS", "writer1=read,odds:write,predictions:write,bets:write;reader1=read"
)
os.environ.setdefault(
    "RATE_LIMIT_ENABLED", "false"
)  # stäng av Redis-rate limit i tester
os.environ.setdefault("ENABLE_TRACING", "false")  # undvik OTel-stök i tester

# Importera appen först nu (den läser env vid import)
from app.main import app  # noqa: E402


# --- Pytest-fixtures ---
@pytest.fixture()
def client():
    # raise_server_exceptions=False => låt testerna asserta på 500 osv (inte raise)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="session")
def writer_headers():
    return {"X-API-Key": "writer1", "content-type": "application/json"}


@pytest.fixture(scope="session")
def reader_headers():
    return {"X-API-Key": "reader1"}


@pytest.fixture()
def make_jwt():
    def _make(scopes, kid="v1", sub="test-client"):
        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "iss": "betting-core",
            "aud": "betting-clients",
            "sub": "sub",
            "scopes": scopes,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(hours=1)).timestamp()),
        }
        key = {"v1": "testsecret1", "v2": "testsecret2"}[kid]
        return jwt.encode(payload, key, algorithm="HS256", headers={"kid": kid})

    return _make
