import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# --- Lägg repo-roten på sys.path ---
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
