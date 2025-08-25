from datetime import datetime
from typing import Iterable
from sqlalchemy.orm import Session
from sqlalchemy import select, text, func
from sqlalchemy.dialects.postgresql import insert

from app.models.odds import Odds
from app.models.selections import Selection
from app.models.markets import Market


def bulk_upsert_odds(db: Session, items: Iterable[dict]) -> dict:
    items = list(items)
    if not items:
        return {"inserted": 0, "updated": 0}

    keys = [
        "match_id",
        "bookmaker_id",
        "selection_id",
        "price",
        "probability",
        "captured_at",
        "source",
        "checksum",
    ]

    rows = [{k: it.get(k) for k in keys} for it in items]
    stmt = insert(Odds.__table__).values(rows)

    stmt = stmt.on_conflict_do_update(
        constraint="uq_odds_snapshot",
        set_={
            "price": stmt.excluded.price,
            "probability": stmt.excluded.probability,
            "source": stmt.excluded.source,
            "checksum": stmt.excluded.checksum,
        },
    ).returning(text("(xmax = 0) AS inserted"))

    res = db.execute(stmt)
    returned = res.fetchall()
    db.commit()

    inserted = sum(1 for r in returned if r.inserted)
    updated = len(returned) - inserted
    return {"inserted": inserted, "updated": updated}


# Anävänds inte för tillfället:
def list_odds(
    db: Session,
    match_id: str | None,
    bookmaker_id: str | None,
    selection_id: str | None,
    limit: int = 100,
    offset: int = 0,
    ts_from: datetime | None = None,
    ts_to: datetime | None = None,
    market_code: str | None = None,
):
    stmt = select(Odds)
    if match_id:
        stmt = stmt.where(Odds.match_id == match_id)
    if bookmaker_id:
        stmt = stmt.where(Odds.bookmaker_id == bookmaker_id)
    if selection_id:
        stmt = stmt.where(Odds.selection_id == selection_id)
    if ts_from:
        stmt = stmt.where(Odds.captured_at >= ts_from)
    if ts_to:
        stmt = stmt.where(Odds.captured_at <= ts_to)
    if market_code:
        stmt = (
            stmt.join(Selection, Selection.selection_id == Odds.selection_id)
            .join(Market, Market.market_id == Selection.market_id)
            .where(Market.code == market_code)
        )

    stmt = (
        stmt.order_by(Odds.captured_at.asc(), Odds.odds_id.asc())
        .limit(limit)
        .offset(offset)
    )
    return db.execute(stmt).scalars().all()


def _odds_base_query(
    match_id: str | None,
    bookmaker_id: str | None,
    selection_id: str | None,
    ts_from: datetime | None,
    ts_to: datetime | None,
    market_code: str | None,
):
    stmt = select(Odds)
    if match_id:
        stmt = stmt.where(Odds.match_id == match_id)
    if bookmaker_id:
        stmt = stmt.where(Odds.bookmaker_id == bookmaker_id)
    if selection_id:
        stmt = stmt.where(Odds.selection_id == selection_id)
    if ts_from:
        stmt = stmt.where(Odds.captured_at >= ts_from)
    if ts_to:
        stmt = stmt.where(Odds.captured_at <= ts_to)
    if market_code:
        stmt = (
            stmt.join(Selection, Selection.selection_id == Odds.selection_id)
            .join(Market, Market.market_id == Selection.market_id)
            .where(Market.code == market_code)
        )
    return stmt


def list_odds_page(
    db,
    match_id: str | None,
    bookmaker_id: str | None,
    selection_id: str | None,
    limit: int = 100,
    offset: int = 0,
    ts_from: datetime | None = None,
    ts_to: datetime | None = None,
    market_code: str | None = None,
):
    base = _odds_base_query(
        match_id, bookmaker_id, selection_id, ts_from, ts_to, market_code
    )
    # total = COUNT(*) över samma filter
    total = db.execute(
        select(func.count()).select_from(base.order_by(None).subquery())
    ).scalar_one()

    # page items
    page_stmt = (
        base.order_by(Odds.captured_at.asc(), Odds.odds_id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(page_stmt).scalars().all()

    next_offset = (offset + limit) if (offset + limit) < total else None
    return rows, total, next_offset
