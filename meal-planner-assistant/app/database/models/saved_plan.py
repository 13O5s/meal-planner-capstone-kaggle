from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class SavedPlan(Base):
    __tablename__ = "saved_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    num_days: Mapped[int] = mapped_column(Integer, nullable=False)
    days_json: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[str] = mapped_column(String(30), nullable=False)
