import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.docs import DEFAULT_ERROR_RESPONSES
from app.schemas.system import ReadyzOut
from app.schemas.errors import ErrorResponse
from app.core.db import engine as _engine, ping_db as _ping_db

engine = _engine  # <- patchbar i tests
ping_db = _ping_db  # <- patchbar i tests


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
        # 1) Ping (patchas i test för att simulera DB-down)
        ping_db()

        with engine.connect() as conn:
            # 2) readiness-vy
            row = conn.execute(
                text("SELECT markets, selections, bookmakers FROM core.readiness")
            ).first()
            if not row:
                # explicit 503 med förväntad code + “readiness” i message
                return JSONResponse(
                    status_code=503,
                    content={
                        "code": "service_unavailable",
                        "message": "readiness view missing",
                    },
                )

            counts = {
                "markets": int(row.markets),
                "selections": int(row.selections),
                "bookmakers": int(row.bookmakers),
            }

            # 3) Alembic revision
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
            return JSONResponse(
                status_code=503,
                content={
                    "code": "service_unavailable",
                    "message": f"readiness: alembic_version mismatch: db={db_rev}, expected={expected}",
                },
            )

        return {
            "status": "ready",
            "db": {"status": "ok", "revision": db_rev, "expected": expected},
            "counts": counts,
        }

    except Exception as e:
        # Generellt readiness-fel: behåll “readiness” i meddelandet
        return JSONResponse(
            status_code=503,
            content={
                "code": "service_unavailable",
                "message": f"readiness error: {e.__class__.__name__}: {e}",
            },
        )
