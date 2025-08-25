from app.core.db import ping_db


def test_ping_db_ok():
    # Kör bara – ska inte kasta
    ping_db()
