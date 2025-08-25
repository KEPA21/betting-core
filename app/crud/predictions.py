from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy import text as _text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.predictions import Prediction


def _predictions_base_query(
    match_id: str | None,
    model_id: str | None,
    version: str | None,
    selection_id: str | None,
):
    stmt = select(Prediction)
    if match_id:
        stmt = stmt.where(Prediction.match_id == match_id)
    if model_id:
        stmt = stmt.where(Prediction.model_id == model_id)
    if version:
        stmt = stmt.where(Prediction.version == version)
    if selection_id:
        stmt = stmt.where(Prediction.selection_id == selection_id)
    return stmt


def list_predictions_page(
    db,
    match_id: str | None,
    model_id: str | None,
    version: str | None,
    selection_id: str | None,
    limit: int = 100,
    offset: int = 0,
):
    base = _predictions_base_query(match_id, model_id, version, selection_id)

    total = db.execute(
        select(func.count()).select_from(base.order_by(None).subquery())
    ).scalar_one()

    page_stmt = (
        base.order_by(Prediction.predicted_at.desc(), Prediction.prediction_id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(page_stmt).scalars().all()

    next_offset = (offset + limit) if (offset + limit) < total else None
    return rows, total, next_offset


UNIQUE_COLS = ["match_id", "model_id", "version", "selection_id"]


def bulk_upsert_predictions(db: Session, rows: list[dict]) -> dict:
    if not rows:
        return {"inserted": 0, "updated": 0}

    # Deduplicera inom batchen – behåll den med senast predicted_at per uniknyckel
    by_key: dict[tuple, dict] = {}
    for r in rows:
        key = (r["match_id"], r["model_id"], r["version"], r["selection_id"])
        pa = r.get("predicted_at")
        if isinstance(pa, str):
            # defensivt: om någon råkar skicka str
            from datetime import datetime

            pa = datetime.fromisoformat(pa.replace("Z", "+00:00"))
        item = {
            "match_id": r["match_id"],
            "model_id": r["model_id"],
            "version": r["version"],
            "selection_id": r["selection_id"],
            "probability": r.get("probability"),
            "odds_fair": r.get("odds_fair"),
            "features": r.get("features"),
            "predicted_at": pa or datetime.utcnow(),
        }
        prev = by_key.get(key)
        if prev is None or item["predicted_at"] >= prev["predicted_at"]:
            by_key[key] = item

    norm = list(by_key.values())
    if not norm:
        return {"inserted": 0, "updated": 0}

    ins = pg_insert(Prediction).values(norm)
    upsert = ins.on_conflict_do_update(
        index_elements=[
            Prediction.match_id,
            Prediction.model_id,
            Prediction.version,
            Prediction.selection_id,
        ],
        set_={
            "probability": ins.excluded.probability,
            "odds_fair": ins.excluded.odds_fair,
            "features": ins.excluded.features,
            "predicted_at": ins.excluded.predicted_at,
        },
    ).returning(_text("(xmax = 0) AS inserted"))

    res = db.execute(upsert).all()
    inserted = sum(1 for (flag,) in res if flag)
    updated = len(res) - inserted
    db.commit()
    return {"inserted": inserted, "updated": updated}
