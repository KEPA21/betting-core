from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from typing import Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import text, bindparam
from uuid import UUID

from app.core.db import get_db
from app.core.security import require_scopes
from app.core.docs import DEFAULT_ERROR_RESPONSES
from app.schemas.bets import BetIn, BetCreateOut
from app.schemas.pages import BetsPage
from app.crud.bets import create_bet, list_bets_page


router = APIRouter()


def _ensure_fk_exists_for_bets(db: Session, rows: list[dict]) -> None:
    if not rows:
        return
    bm_ids = sorted({UUID(str(r["bookmaker_id"])) for r in rows})
    sel_ids = sorted({UUID(str(r["selection_id"])) for r in rows})
    missing = []

    if bm_ids:
        stmt = text(
            "SELECT bookmaker_id FROM core.bookmakers WHERE bookmaker_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        existing = {x[0] for x in db.execute(stmt, {"ids": bm_ids})}
        miss = [str(x) for x in bm_ids if x not in existing]
        if miss:
            missing.append(f"unknown bookmaker_id(s): {', '.join(miss)}")

    if sel_ids:
        stmt = text(
            "SELECT selection_id FROM core.selections WHERE selection_id IN :ids"
        ).bindparams(bindparam("ids", expanding=True))
        existing = {x[0] for x in db.execute(stmt, {"ids": sel_ids})}
        miss = [str(x) for x in sel_ids if x not in existing]
        if miss:
            missing.append(f"unknown selection_id(s): {', '.join(miss)}")

    if missing:
        raise HTTPException(status_code=404, detail="; ".join(missing))


@router.post(
    "/bets",
    tags=["bets"],
    summary="Skapa bet (idempotent)",
    response_model=BetCreateOut,
    responses={
        **DEFAULT_ERROR_RESPONSES,
        201: {"description": "OK"},
        200: {"description": "Idempotent duplicate"},
    },
    dependencies=[Depends(require_scopes("bets:write"))],
)
def post_bet(payload: BetIn, db: Session = Depends(get_db), response: Response = None):
    row = payload.model_dump()
    _ensure_fk_exists_for_bets(db, [row])
    result = create_bet(db, row)
    if response is not None:
        response.status_code = (
            status.HTTP_201_CREATED if result.get("created") else status.HTTP_200_OK
        )
    return result


@router.get(
    "/bets",
    tags=["bets"],
    summary="Lista bets",
    response_model=BetsPage,
    responses={**DEFAULT_ERROR_RESPONSES, 200: {"description": "OK"}},
    dependencies=[Depends(require_scopes("read"))],
)
def get_bets(
    user_ref: Optional[str] = None,
    bet_status: Optional[Literal["open", "won", "lost", "void", "settled"]] = Query(
        None, alias="status"
    ),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    rows, total, next_offset = list_bets_page(db, user_ref, status, limit, offset)
    return {
        "items": [
            {
                "bet_id": str(r.bet_id),
                "external_id": r.external_id,
                "user_ref": r.user_ref,
                "match_id": r.match_id,
                "bookmaker_id": str(r.bookmaker_id),
                "selection_id": str(r.selection_id),
                "stake": float(r.stake),
                "price": float(r.price),
                "placed_at": r.placed_at.isoformat(),
                "status": r.status,
                "result": r.result,
                "payout": float(r.payout) if r.payout is not None else None,
                "idempotency_key": r.idempotency_key,
            }
            for r in rows
        ],
        "total": int(total),
        "next_offset": next_offset,
    }
