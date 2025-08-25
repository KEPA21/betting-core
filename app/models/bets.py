from __future__ import annotations
from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class Bet(Base):
    __tablename__ = "bets"

    bet_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    external_id: Mapped[str | None] = mapped_column(String)
    user_ref: Mapped[str | None] = mapped_column(String)
    match_id: Mapped[str] = mapped_column(String, nullable=False)
    bookmaker_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.bookmakers.bookmaker_id"), nullable=False
    )
    selection_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.selections.selection_id"), nullable=False
    )
    stake: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    placed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, server_default=text("'open'"), nullable=False
    )
    result: Mapped[str | None] = mapped_column(String)
    payout: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    idempotency_key: Mapped[str | None] = mapped_column(
        String
    )  # unik i DB via constraint
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()"), nullable=False
    )
