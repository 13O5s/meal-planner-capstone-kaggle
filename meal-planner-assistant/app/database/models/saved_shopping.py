from __future__ import annotations

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class SavedShoppingList(Base):
    __tablename__ = "saved_shopping_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[str] = mapped_column(String(30), nullable=False)


class SavedShoppingItem(Base):
    __tablename__ = "saved_shopping_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    list_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    already_have: Mapped[float] = mapped_column(Float, nullable=False)
    need: Mapped[float] = mapped_column(Float, nullable=False)
    purchased: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
