from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
#from .base import APISchema

class OddsIn(BaseModel):
    match_id: str
    bookmaker_id: UUID
    selection_id: UUID
    price: float = Field(gt=1.0)
    probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    captured_at: datetime
    source: Optional[str] = None
    checksum: Optional[str] = None

class OddsBulkIn(BaseModel):
    items: List[OddsIn]


# Enskilt odds
OddsIn.model_config = {
    "json_schema_extra": {
        "examples": [{
            "match_id":"m1",
            "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
            "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
            "price": 2.04,
            "probability": 0.49,
            "captured_at": "2025-08-18T12:00:00Z",
            "source": "feed-x"
        }]
    }
}

# Bulk payload
OddsBulkIn.model_config = {
    "json_schema_extra": {
        "examples": [{
            "items": [
                {
                    "match_id": "m1",
                    "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
                    "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
                    "price": 2.04,
                    "probability": 0.49,
                    "captured_at": "2025-08-18T12:00:00Z",
                    "source": "feed-x"
                },
                {
                    "match_id": "m1",
                    "bookmaker_id": "024c6a47-1a14-4549-935f-31e22e747670",
                    "selection_id": "bea8671c-e889-4e3d-91d3-b407bc186408",
                    "price": 1.95,
                    "probability": 0.51,
                    "captured_at": "2025-08-18T12:05:00Z",
                    "source": "feed-x"
                }
            ]
        }]
    }
}