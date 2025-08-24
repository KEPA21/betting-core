from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, text, func
from app.models.bets import Bet


def list_bets_page(
    db,
    user_ref: str | None,
    status: str | None,
    limit: int = 100,
    offset: int = 0,
):
    base = select(Bet)
    if user_ref:
        base = base.where(Bet.user_ref == user_ref)
    if status:
        base = base.where(Bet.stats == status)

    total = db.execute(
        select(func.count()).select_from(base.order_by(None).subquery())
    ).scalar_one()

    page_stmt = (
        base.order_by(Bet.placed_at.desc(), Bet.bet_id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(page_stmt).scalars().all()

    next_offset = (offset + limit) if (offset + limit) < total else None
    return rows, total, next_offset


def create_bet(db: Session, data: Dict[str, Any]) -> dict:
    """
    Idempotent create:
    - Om idempotency_key: ON CONFLICT (idempotency_key) DO NOTHING
    - Annars om (user_ref, external_id): ON CONFLICT (user_ref, external_id WHERE external_id IS NOT NULL) DO NOTHING
    Returnerar {"created": bool, "bet_id": UUID}
    """

    # Obligatoriska/vanliga fält – ta med bara om de har värde
    base_keys = [
        "external_id",
        "user_ref",
        "match_id",
        "bookmaker_id",
        "selection_id",
        "stake",
        "price",
        "placed_at",
        "idempotency_key",
    ]
    row = {k: data[k] for k in base_keys if k in data and data[k] is not None}

    # Valfria fält: inkludera ENDAST om de satts (annars får vi NULL och bryter NOT NULL/default)
    for k in ("status", "result", "payout"):
        v = data.get(k)
        if v is not None:
            row[k] = v
    # OBS: Om status inte skickas → DB default 'open' gäller.

    stmt = insert(Bet.__table__).values(row)

    if row.get("idempotency_key"):
        stmt = stmt.on_conflict_do_nothing(index_elements=["idempotency_key"])
    elif row.get("external_id") and row.get("user_ref"):
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["user_ref", "external_id"],
            index_where=text("external_id IS NOT NULL"),
        )

    stmt = stmt.returning(Bet.__table__.c.bet_id, text("(xmax = 0) AS inserted"))

    res = db.execute(stmt)
    returned = res.first()
    db.commit()

    if returned and returned.inserted:
        return {"created": True, "bet_id": returned.bet_id}

    # Inte insatt → leta upp befintlig rad enligt idempotens-nyckel
    if row.get("idempotency_key"):
        q = (
            select(Bet.bet_id)
            .where(Bet.idempotency_key == row["idempotency_key"])
            .limit(1)
        )
    elif row.get("external_id") and row.get("user_ref"):
        q = (
            select(Bet.bet_id)
            .where(
                Bet.user_ref == row["user_ref"], Bet.external_id == row["external_id"]
            )
            .limit(1)
        )
    else:
        return {"created": False, "bet_id": None}

    existing = db.execute(q).first()
    return {"created": False, "bet_id": existing.bet_id if existing else None}


def list_bets(
    db: Session,
    user_ref: Optional[str],
    status: Optional[str],
    limit: int = 100,
    offset: int = 0,
):
    q = select(Bet)
    if user_ref:
        q = q.where(Bet.user_ref == user_ref)
    if status:
        q = q.where(Bet.status == status)
    q = q.order_by(Bet.placed_at.desc()).limit(limit).offset(offset)
    return db.execute(q).scalars().all()
