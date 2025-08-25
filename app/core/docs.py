from app.schemas.errors import ErrorResponse

DEFAULT_ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "No/invalid API key"},
    403: {"model": ErrorResponse, "description": "Insufficient scope"},
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    429: {"model": ErrorResponse, "description": "Rate limit"},
    500: {"model": ErrorResponse, "description": "Server error"},
}
