# tests/conftest.py
import os
import sys
import jwt
import datetime as dt
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# --- Lägg repo-roten på sys.path ---
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Tvinga testvänlig auth innan appen importeras (OBS: direkta tilldelningar) ---
os.environ["AUTH_MODE"] = "both"
os.environ["API_KEYS"] = (
    "writer1=read,odds:write,predictions:write,bets:write;reader1=read"
)
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENABLE_TRACING"] = "false"

# JWT-konfig
os.environ["JWT_ALG"] = "HS256"
os.environ["JWT_ISSUER"] = "betting-core"
os.environ["JWT_AUDIENCE"] = "betting-clients"
os.environ["JWT_SECRETS"] = "v1:testsecret1,v2:testsecret2"
os.environ["JWT_ACCEPTED_KIDS"] = "v1,v2"

from app.main import app  # noqa: E402


# --- Pytest-fixtures ---
@pytest.fixture()
def client():
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
        # säkerställ lista
        scopes_list = [scopes] if isinstance(scopes, str) else list(scopes)

        now = dt.datetime.now(dt.timezone.utc)
        payload = {
            "iss": os.environ["JWT_ISSUER"],
            "aud": os.environ["JWT_AUDIENCE"],
            "sub": sub,
            "scopes": scopes_list,
            "iat": int(now.timestamp()),
            "exp": int((now + dt.timedelta(hours=1)).timestamp()),
        }
        key = {"v1": "testsecret1", "v2": "testsecret2"}[kid]
        return jwt.encode(
            payload, key, algorithm=os.environ["JWT_ALG"], headers={"kid": kid}
        )

    return _make


@pytest.fixture()
def jwt_read_headers(make_jwt):
    token = make_jwt(["read"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def jwt_writer_headers(make_jwt):
    token = make_jwt(["read", "odds:write", "predictions:write", "bets:write"])
    return {"Authorization": f"Bearer {token}", "content-type": "application/json"}
