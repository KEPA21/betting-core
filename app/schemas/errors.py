from typing import List, Optional
from .base import APISchema


class FieldError(APISchema):
    field: str  # t.ex. "items.0.price"
    message: str  # t.ex. "Input should be a valid number"


class ErrorResponse(APISchema):
    code: str  # t.ex. "validation_error", "unauthorized", "forbidden", "internal_error"
    message: str  # kort beskrivning
    fieldErrors: Optional[List[FieldError]] = None
    traceId: str  # korrelations-ID för loggar
