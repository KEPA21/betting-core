from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey, text
from .base import Base


class Selection(Base):
    __tablename__ = "selections"

    selection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()")
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("core.markets.market_id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String, nullable=False)
