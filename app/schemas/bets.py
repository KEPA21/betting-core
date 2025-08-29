from __future__ import annotations
from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import APISchema


class BetIn(APISchema):
    external_id: Optional[str] = None
    user_ref: Optional[str] = None
    match_id: str
    bookmaker_id: UUID
    selection_id: UUID
    stake: float = Field(gt=0)
    price: float = Field(gt=1.0)
    placed_at: datetime
    idempotency_key: Optional[str] = None


class BetCreateOut(APISchema):
    created: bool
    bet_id: Optional[UUID] = None


# (Valfritt men bra för tydlighet i list-svar)
class BetOut(APISchema):
    bet_id: UUID
    external_id: Optional[str] = None
    user_ref: Optional[str] = None
    match_id: str
    bookmaker_id: UUID
    selection_id: UUID
    stake: float
    price: float
    # Om din BetsPage (i pages.py) definierar placed_at som str -> byt här till str
    placed_at: datetime
    status: str
    result: Optional[str] = None
    payout: Optional[float] = None
    idempotency_key: Optional[str] = None


BetIn.model_config = {
    "json_schema_extra": {
        "examples": [
            {
                "external_id": "ticket-123",
                "user_ref": "user42",
                "match_id": "m1",
                "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
                "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
                "stake": 100.0,
                "price": 2.10,
                "placed_at": "2025-08-18T12:30:00Z",
                "idempotency_key": "abc-123",
            }
        ]
    }
}
