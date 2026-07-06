from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, TimestampMixin


class Ingredient(TimestampMixin, Base):
    __tablename__ = "ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(30))
    default_unit: Mapped[str] = mapped_column(
        String(20), nullable=False, default="g"
    )
    seasonal: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    __table_args__ = (
        CheckConstraint(
            "category IN ('Fruits', 'Vegetables', 'Meat', 'Seafood', 'Dairy', 'Eggs', 'Grains', "
            "'Legumes', 'Nuts & Seeds', 'Herbs & Spices', 'Oils & Fats', 'Pantry', "
            "'Frozen', 'Beverages', 'Bakery', 'Snacks')",
            name="chk_ingredients_category",
        ),
    )

    aliases: Mapped[list[IngredientAlias]] = relationship(
        back_populates="ingredient", cascade="all, delete-orphan"
    )
    nutrition: Mapped[IngredientNutrition] = relationship(
        back_populates="ingredient",
        uselist=False,
        cascade="all, delete-orphan",
    )


class IngredientAlias(CreatedAtMixin, Base):
    __tablename__ = "ingredient_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    ingredient: Mapped[Ingredient] = relationship(back_populates="aliases")


class IngredientNutrition(TimestampMixin, Base):
    __tablename__ = "ingredient_nutrition"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    calories_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    protein_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    carbohydrates_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    fat_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    fiber_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    sugar_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )
    sodium_per_100g: Mapped[float] = mapped_column(
        Numeric(7, 1), nullable=False, default=0
    )

    __table_args__ = (
        CheckConstraint(
            "calories_per_100g >= 0",
            name="chk_ingredient_nutrition_calories",
        ),
        CheckConstraint(
            "protein_per_100g >= 0",
            name="chk_ingredient_nutrition_protein",
        ),
        CheckConstraint(
            "carbohydrates_per_100g >= 0",
            name="chk_ingredient_nutrition_carbs",
        ),
        CheckConstraint(
            "fat_per_100g >= 0", name="chk_ingredient_nutrition_fat"
        ),
    )

    ingredient: Mapped[Ingredient] = relationship(back_populates="nutrition")
