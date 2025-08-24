from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam
from uuid import UUID

from app.schemas.odds import OddsBulkIn
from app.schemas.pages import OddsPage
from app.core.db import get_db
from app.core.docs import DEFAULT_ERROR_RESPONSES
from app.core.pagination import encode_cursor, decode_cursor
from app.core.ratelimit import per_key_limiter, global_limiter, noop_dependency
from app.crud.odds import bulk_upsert_odds
from app.core.settings import settings
from app.core.security import require_scopes


router = APIRouter()

if settings.RATE_LIMIT_ENABLED:
    _limit_odds_per_key = per_key_limiter(
        "odds_post",
        capacity=settings.RL_ODDS_PER_KEY_CAP,
        refill_per_sec=settings.RL_ODDS_PER_KEY_REFILL,
    )
    _limit_odds_global = global_limiter(
        "odds_post",
        capacity=settings.RL_ODDS_GLOBAL_CAP,
        refill_per_sec=settings.RL_ODDS_GLOBAL_REFILL,
    )
else:
    _limit_odds_per_key = noop_dependency
    _limit_odds_global = noop_dependency


def _ensure_fk_exists_for_odds(db: Session, rows: list[dict]) -> None:
    if not rows:
        return

    bm_ids = sorted({UUID(str(r["bookmaker_id"])) for r in rows})
    sel_ids = sorted({UUID(str(r["selection_id"])) for r in rows})

    missing_parts = []

    if bm_ids:
        stmt_bm = text(
            "SELECT bookmaker_id FROM core.bookmakers WHERE bookmaker_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        existing_bm = {x[0] for x in db.execute(stmt_bm, {"ids": bm_ids})}
        missing_bm = [str(b) for b in bm_ids if b not in existing_bm]
        if missing_bm:
            missing_parts.append(f"unknown bookmaker_id(s): {', '.join(missing_bm)}")

    if sel_ids:
        stmt_sel = text(
            "SELECT selection_id FROM core.selections WHERE selection_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        existing_sel = {x[0] for x in db.execute(stmt_sel, {"ids": sel_ids})}
        missing_sel = [str(s) for s in sel_ids if s not in existing_sel]
        if missing_sel:
            missing_parts.append(f"unknown selection_id(s): {', '.join(missing_sel)}")

    if missing_parts:
        raise HTTPException(status_code=404, detail="; ".join(missing_parts))


@router.post(
    "/odds",
    summary="Bulk upsert odds",
    description="Tar emot en lista av odds-snapshots och upsertar dem mot unik nyckel (match_id, bookmaker_id, selection_id, captured_at).",
    responses={**DEFAULT_ERROR_RESPONSES, 200: {"description": "OK"}},
    dependencies=[
        Depends(require_scopes("odds:write")),
        Depends(_limit_odds_per_key),
        Depends(_limit_odds_global),
    ],
)
def post_odds(payload: OddsBulkIn, db: Session = Depends(get_db)):
    rows = [o.model_dump() for o in payload.items]
    _ensure_fk_exists_for_odds(db, rows)  # 404 om model_id/selection_id saknas
    result = bulk_upsert_odds(db, rows)  # återanvänd rows
    return result


@router.get(
    "/odds",
    tags=["odds"],
    summary="Lista odds",
    response_model=OddsPage,
    responses={**DEFAULT_ERROR_RESPONSES, 200: {"description": "OK"}},
    dependencies=[Depends(require_scopes("read"))],
)
def get_odds(
    match_id: str | None = None,
    bookmaker_id: UUID | None = None,
    selection_id: UUID | None = None,
    ts_from: datetime | None = Query(None, alias="ts_from"),
    ts_to: datetime | None = Query(None, alias="ts_to"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    cursor: str | None = Query(None),
    sort: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    where_base = ["1=1"]
    params: dict = {}

    if match_id:
        where_base.append("match_id = :match_id")
        params["match_id"] = match_id
    if bookmaker_id:
        where_base.append("bookmaker_id = :bookmaker_id")
        params["bookmaker_id"] = bookmaker_id
    if selection_id:
        where_base.append("selection_id = :selection_id")
        params["selection_id"] = selection_id
    if ts_from:
        where_base.append("captured_at >= :ts_from")
        params["ts_from"] = ts_from
    if ts_to:
        where_base.append("captured_at <= :ts_to")
        params["ts_to"] = ts_to  # <-- fix

    # total: utan cursor
    where_base_sql = " AND ".join(where_base)
    total = db.execute(
        text(f"SELECT COUNT(*) FROM core.odds WHERE {where_base_sql}"), params
    ).scalar_one()

    # cursor: läggs ovanpå basfiltren
    where = list(where_base)
    order = "ASC" if sort == "asc" else "DESC"
    cmp = ">" if sort == "asc" else "<"

    if cursor:
        try:
            cur_ts, cur_id = decode_cursor(cursor)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid cursor")
        where.append(f"(captured_at, odds_id) {cmp} (:cur_ts, :cur_id)")
        params["cur_ts"] = cur_ts
        params["cur_id"] = cur_id

    where_sql = " AND ".join(where)
    order_clause = f"captured_at {order}, odds_id {order}"

    # Använd OFFSET bara när vi inte kör med cursor
    offset_clause = "" if cursor else "OFFSET :offset"

    items_sql = text(
        f"""
        SELECT odds_id, match_id, bookmaker_id, selection_id, price,
               probability, captured_at, source, checksum, created_at
        FROM core.odds
        WHERE {where_sql}
        ORDER BY {order_clause}
        LIMIT :limit
        {offset_clause}
    """
    )

    exec_params = {**params, "limit": limit}
    if not cursor:
        exec_params["offset"] = offset

    rows = db.execute(items_sql, exec_params).mappings().all()

    items = [
        {
            "odds_id": str(r["odds_id"]),
            "match_id": r["match_id"],
            "bookmaker_id": str(r["bookmaker_id"]),
            "selection_id": str(r["selection_id"]),
            "price": float(r["price"]),
            "probability": (
                float(r["probability"]) if r["probability"] is not None else None
            ),
            "captured_at": r["captured_at"].isoformat(),
            "source": r["source"],
            "checksum": r["checksum"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]

    next_cursor = None
    if len(rows) == limit:
        last = rows[-1]
        next_cursor = encode_cursor(last["captured_at"], last["odds_id"])

    next_offset = None
    if not cursor:
        no = offset + len(items)
        next_offset = no if no < total else None

    return {
        "items": items,
        "total": total,
        "next_cursor": next_cursor,
        "next_offset": next_offset,
    }
