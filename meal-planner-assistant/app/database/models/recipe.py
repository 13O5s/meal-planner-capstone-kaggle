from __future__ import annotations

# ruff: noqa: F821 — SQLAlchemy lazy forward references
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, TimestampMixin


class Recipe(TimestampMixin, Base):
    __tablename__ = "recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    servings: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )
    prep_time_minutes: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )
    cook_time_minutes: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0
    )
    difficulty: Mapped[str | None] = mapped_column(String(10))
    cuisine: Mapped[str | None] = mapped_column(String(50))
    image_url: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    __table_args__ = (
        CheckConstraint("servings > 0", name="chk_recipes_servings"),
        CheckConstraint(
            "prep_time_minutes >= 0", name="chk_recipes_prep_time"
        ),
        CheckConstraint(
            "cook_time_minutes >= 0", name="chk_recipes_cook_time"
        ),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="chk_recipes_difficulty",
        ),
    )

    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    nutrition: Mapped[RecipeNutrition] = relationship(
        back_populates="recipe",
        uselist=False,
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[RecipeTag]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(CreatedAtMixin, Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    optional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_recipe_ingredients_qty"),
        UniqueConstraint(
            "recipe_id", "ingredient_id", name="uq_recipe_ingredients"
        ),
    )

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()


class RecipeNutrition(TimestampMixin, Base):
    __tablename__ = "recipe_nutrition"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    calories: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    protein: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    carbohydrates: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    fat: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    fiber: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    sugar: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )
    sodium: Mapped[float] = mapped_column(
        Numeric(8, 1), nullable=False, default=0
    )

    recipe: Mapped[Recipe] = relationship(back_populates="nutrition")


class Tag(CreatedAtMixin, Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )

    recipes: Mapped[list[RecipeTag]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class RecipeTag(CreatedAtMixin, Base):
    __tablename__ = "recipe_tags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="RESTRICT"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("recipe_id", "tag_id", name="uq_recipe_tags"),
    )

    recipe: Mapped[Recipe] = relationship(back_populates="tags")
    tag: Mapped[Tag] = relationship(back_populates="recipes")
