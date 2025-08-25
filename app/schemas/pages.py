from pydantic import Field
from typing import List, Optional
from .base import APISchema


class OddsItem(APISchema):
    odds_id: str
    match_id: str
    bookmaker_id: str
    selection_id: str
    price: float
    probability: float | None
    captured_at: str
    source: str | None
    checksum: str | None
    created_at: str | None


class OddsPage(APISchema):
    items: List[OddsItem]
    total: int
    next_cursor: Optional[str] = None
    next_offset: Optional[int]


class PredictionItem(APISchema):
    prediction_id: str
    match_id: str
    model_id: str
    version: str
    selection_id: str
    probability: float
    odds_fair: float | None = None
    features: dict = Field(default_factory=dict)  # undvik None -> {} i output
    predicted_at: str  # eller datetime om du vill (se punkt 2 nedan)


class PredictionsPage(APISchema):
    items: List[PredictionItem]
    total: int
    next_cursor: Optional[str] = None
    next_offset: Optional[int] = None


class BetItem(APISchema):
    bet_id: str
    external_id: str | None
    user_ref: str | None
    match_id: str
    bookmaker_id: str
    selection_id: str
    stake: float
    price: float
    placed_at: str
    status: str
    result: str | None
    payout: float | None
    idempotency_key: str | None


class BetsPage(APISchema):
    items: List[BetItem]
    total: int
    next_offset: Optional[int]
