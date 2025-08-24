# app/routers/health.py
from fastapi import APIRouter
from app.schemas.system import HealthzOut
from app.core.docs import DEFAULT_ERROR_RESPONSES

router = APIRouter()


@router.get(
    "/healthz",
    tags=["system"],
    summary="Snabb hälsokoll",
    response_model=HealthzOut,
    responses={
        200: {"description": "Service is healthy"},
        **DEFAULT_ERROR_RESPONSES,  # konsekvent felmodell i specen
    },
)
def healthz():
    return {"status": "ok"}
