from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, text
from .base import Base

class Market(Base):
    __tablename__ = "markets"

    market_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    code: Mapped[str] = mapped_column(String, nullable=False)