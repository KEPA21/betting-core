from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base

class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_gereate_v4()")
    )
    match_id: Mapped[str] = mapped_column(String, nullable=False)
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("core.models.model_id"), nullable=False
    )
    version: Mapped[str] = mapped_column(String, nullable=False)
    selection_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("core.selections.selection_id"), nullable=False
    )
    probability: Mapped[float] = mapped_column(Numeric(7,6), nullable=False)
    odds_fair: Mapped[float | None] = mapped_column(Numeric(10,4))
    features: Mapped[dict | None] = mapped_column(JSONB)
    predicted_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )