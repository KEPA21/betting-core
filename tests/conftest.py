import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from fastapi.testclient import TestClient
from app.main import app

os.environ.setdefault("API_KEYS", "writer1=read,odds:write,predictions:write,bets:write;reader1=read")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("ENABLE_TRACING", "false")

@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="session")
def writer_headers():
    return {"X-API-Key": "writer1", "content-type": "application/json"}

@pytest.fixture(scope="session")
def reader_headers():
    return {"X-API-Key": "reader1"}