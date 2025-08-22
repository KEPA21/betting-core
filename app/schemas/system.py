from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

class HealthzOut(BaseModel):
    status: Literal["ok"]
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

class ReadyzDb(BaseModel):
    status: Literal["ok"]
    revision: Optional[str] = None
    expected: Optional[str] = None

class ReadyzCounts(BaseModel):
    markets: int
    selections: int
    bookmakers: int

class ReadyzOut(BaseModel):
    status: Literal["ready"]
    db: ReadyzDb
    counts: ReadyzCounts
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "db": {"status": "ok", "revision": "33dd3a3de106", "expected": "33dd3a3de106"},
                "counts": {"markets": 3, "selections": 12, "bookmakers": 2},
            }
        }
    )