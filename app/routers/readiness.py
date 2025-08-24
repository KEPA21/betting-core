# app/routers/readiness.py
import os
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.core.db import engine
from app.core.docs import DEFAULT_ERROR_RESPONSES
from app.schemas.system import ReadyzOut
from app.schemas.errors import ErrorResponse

router = APIRouter()


@router.get(
    "/readyz",
    tags=["system"],
    summary="Readiness mot DB (ping + counts + migrationsnivå)",
    response_model=ReadyzOut,
    responses={
        200: {"description": "Application is ready"},
        503: {"model": ErrorResponse, "description": "Not ready (DB/migration)"},
        **DEFAULT_ERROR_RESPONSES,
    },
)
def readyz():
    try:
        with engine.connect() as conn:
            # Ping
            conn.execute(text("SELECT 1"))

            # Counts från readiness-vy
            row = conn.execute(
                text("SELECT markets, selections, bookmakers FROM core.readiness")
            ).first()
            if not row:
                raise HTTPException(status_code=503, detail="readiness view missing")

            counts = {
                "markets": int(row.markets),
                "selections": int(row.selections),
                "bookmakers": int(row.bookmakers),
            }

            # Alembic revision
            db_rev = conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()

        expected = os.getenv("ALEMBIC_EXPECTED_REV")
        strict = os.getenv("READYZ_STRICT_MIGRATIONS", "true").lower() in (
            "1",
            "true",
            "yes",
        )

        if expected and db_rev != expected and strict:
            raise HTTPException(
                status_code=503,
                detail=f"alembic_version mismatch: db={db_rev}, expected={expected}",
            )

        return {
            "status": "ready",
            "db": {"status": "ok", "revision": db_rev, "expected": expected},
            "counts": counts,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"db_not_ready: {e.__class__.__name__}: {e}"
        )
