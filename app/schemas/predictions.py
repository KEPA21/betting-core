from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import Field
from .base import APISchema

class PredictionIn(APISchema):
    match_id: str
    model_id: UUID
    version: str = "v1"
    selection_id: UUID
    probability: float = Field(ge=0.0, le=1.0)
    odds_fair: Optional[float] = Field(default=None, gt=1.0)
    features: Optional[Dict[str, Any]] = None
    predicted_at: datetime

class PredictionsBulkIn(APISchema):
    items: List[PredictionIn]

class PredictionOut(APISchema):
    prediction_id: str
    match_id: str
    model_id: str
    version: str
    selection_id: str
    probability: float | None = None
    odds_fair: float | None = None
    features: dict[str, Any] = Field(default_factory=dict)
    predicted_at: str


PredictionIn.model_config = {
    "json_schema_extra": {
        "examples": [{
            "match_id": "m1",
            "model_id": "00000000-0000-0000-0000-000000000001",
            "version": "1.0",
            "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
            "probability": 0.58,
            "odds_fair": 1.72,
            "features": {"home_form": 0.65}
        }]
    }
}
