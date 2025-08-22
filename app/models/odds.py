from __future__ import annotations
from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, TIMESTAMP, ForeignKey, text

from .base import Base

class Odds(Base):
    __tablename__ = "odds"

    odds_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("uuid_generate_v4()")
    )
    match_id: Mapped[str] = mapped_column(String, nullable=False)
    bookmaker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core.bookmakers.bookmaker_id"), nullable=False
    )
    selection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("core.selections.selection_id"), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10,4), nullable=False)
    probability: Mapped[Decimal | None] = mapped_column(Numeric(7,6))
    captured_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    source: Mapped[str | None] = mapped_column(String)
    checksum: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )