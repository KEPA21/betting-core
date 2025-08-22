from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam
from uuid import UUID

from app.schemas.predictions import PredictionsBulkIn
from app.schemas.pages import PredictionsPage
from app.schemas.errors import ErrorResponse
from app.core.db import get_db
from app.core.security import require_scopes
from app.core.docs import DEFAULT_ERROR_RESPONSES
from app.core.pagination import encode_cursor, decode_cursor
from app.crud.predictions import bulk_upsert_predictions

router = APIRouter()

def _ensure_fk_exists_for_predictions(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    model_ids = sorted({UUID(str(r["model_id"])) for r in rows})
    sel_ids   = sorted({UUID(str(r["selection_id"])) for r in rows})

    missing = []

    if model_ids:
        stmt = text("SELECT model_id FROM core.models WHERE model_id IN :ids").bindparams(
            bindparam("ids", expanding=True)
        )
        existing = {x[0] for x in db.execute(stmt, {"ids": model_ids})}
        miss = [str(x) for x in model_ids if x not in existing]
        if miss:
            missing.append(f"unknown model_id(s): {', '.join(miss)}")

    if sel_ids:
        stmt = text("SELECT selection_id FROM core.selections WHERE selection_id IN :ids").bindparams(
            bindparam("ids", expanding=True)
        )
        existing = {x[0] for x in db.execute(stmt, {"ids": sel_ids})}
        miss = [str(x) for x in sel_ids if x not in existing]
        if miss:
            missing.append(f"unknown selection_id(s): {', '.join(miss)}")

    if missing:
        raise HTTPException(status_code=404, detail="; ".join(missing))

@router.post(
    "/predictions",
    tags=["predictions"],
    summary="Bulk upsert predictions",
    responses={**DEFAULT_ERROR_RESPONSES, 200: {"description": "OK"}},
    dependencies=[Depends(require_scopes("predictions:write"))],
)
def post_predictions(payload: PredictionsBulkIn, db: Session = Depends(get_db)):
    rows = [o.model_dump() for o in payload.items]
    _ensure_fk_exists_for_predictions(db, rows)   # 404 om model_id/selection_id saknas
    result = bulk_upsert_predictions(db, rows)
    return result

@router.get(
    "/predictions",
    tags=["predictions"],
    summary="Lista predictions",
    response_model=PredictionsPage,
    dependencies=[Depends(require_scopes("read"))],
    responses={**DEFAULT_ERROR_RESPONSES, 200: {"description": "OK"}},
)
def get_predictions(
    db: Session = Depends(get_db),
    match_id: str | None = None,
    model_id: UUID | None = None,
    version: str | None = None,
    selection_id: UUID | None = None,
    ts_from: datetime | None = Query(None, alias="ts_from"),
    ts_to: datetime | None = Query(None, alias="ts_to"),
    limit: int = Query(100, ge=1, le=1000),
    cursor: str | None = Query(None),
    offset: int = Query(0, ge=0),
    sort: str = Query("asc", pattern="^(asc|desc)$"),
):
    where = ["1=1"]
    params: dict = {}
    if match_id:     where.append("match_id = :match_id");         params["match_id"] = match_id
    if model_id:     where.append("model_id = :model_id");         params["model_id"] = model_id
    if version:      where.append("version = :version");           params["version"] = version
    if selection_id: where.append("selection_id = :selection_id"); params["selection_id"] = selection_id
    if ts_from:      where.append("predicted_at >= :ts_from");     params["ts_from"] = ts_from
    if ts_to:        where.append("predicted_at <= :ts_to");       params["ts_to"] = ts_to

    order = "ASC" if sort == "asc" else "DESC"
    cmp   = ">" if sort == "asc" else "<"
    order_clause = f"predicted_at {order}, prediction_id {order}"

    # total utan cursor
    where_base_sql = " AND ".join(where)
    total = db.execute(text(f"SELECT COUNT(*) FROM core.predictions WHERE {where_base_sql}"), params).scalar_one()

    # cursorfilter ovanpå basen
    if cursor:
        try:
            cur_ts, cur_id = decode_cursor(cursor)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid cursor")
        where.append(f"(predicted_at, prediction_id) {cmp} (:cur_ts, :cur_id)")
        params["cur_ts"] = cur_ts
        params["cur_id"] = cur_id

    where_sql = " AND ".join(where)
    offset_clause = "" if cursor else "OFFSET :offset"

    items_sql = text(f"""
        SELECT prediction_id, match_id, model_id, version, selection_id,
               probability, odds_fair, features, predicted_at
        FROM core.predictions
        WHERE {where_sql}
        ORDER BY {order_clause}
        LIMIT :limit
        {offset_clause}
    """)

    exec_params = {**params, "limit": limit}
    if not cursor:
        exec_params["offset"] = offset

    rows = db.execute(items_sql, exec_params).mappings().all()

    items = [{
        "prediction_id": str(r["prediction_id"]),
        "match_id": r["match_id"],
        "model_id": str(r["model_id"]),
        "version": r["version"],
        "selection_id": str(r["selection_id"]),
        "probability": float(r["probability"]) if r["probability"] is not None else None,
        "odds_fair": float(r["odds_fair"]) if r["odds_fair"] is not None else None,
        "features": r["features"] or {},
        "predicted_at": r["predicted_at"].isoformat(),  # låt Pydantic serialisera datetime
    } for r in rows]

    next_cursor = None
    if len(rows) == limit:
        last = rows[-1]
        next_cursor = encode_cursor(last["predicted_at"], last["prediction_id"])

    next_offset = None
    if not cursor:
        no = offset + len(items)
        next_offset = no if no < total else None

    return {"items": items, "total": int(total), "next_cursor": next_cursor, "next_offset": next_offset}
