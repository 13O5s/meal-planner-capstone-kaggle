from __future__ import annotations

# ruff: noqa: F821 — SQLAlchemy lazy forward references
import uuid
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin


class MealHistory(CreatedAtMixin, Base):
    __tablename__ = "meal_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    rating: Mapped[int | None] = mapped_column(SmallInteger)

    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="chk_meal_history_rating",
        ),
        UniqueConstraint(
            "user_id", "recipe_id", "date", name="uq_meal_history"
        ),
    )

    user: Mapped[User] = relationship(back_populates="meal_history")
    recipe: Mapped[Recipe] = relationship()


class FavoriteRecipe(CreatedAtMixin, Base):
    __tablename__ = "favorite_recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="RESTRICT"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "recipe_id", name="uq_favorite_recipes"
        ),
    )

    user: Mapped[User] = relationship(back_populates="favorite_recipes")
    recipe: Mapped[Recipe] = relationship()
