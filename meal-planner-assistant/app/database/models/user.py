from __future__ import annotations

# ruff: noqa: F821 — SQLAlchemy lazy forward references
import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, CreatedAtMixin, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    account_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )

    __table_args__ = (
        CheckConstraint(
            "account_status IN ('active', 'inactive', 'suspended', 'deleted')",
            name="chk_users_account_status",
        ),
    )

    profile: Mapped[UserProfile] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    food_preferences: Mapped[list[FoodPreference]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    dietary_restrictions: Mapped[list[DietaryRestriction]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    allergies: Mapped[list[UserAllergy]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    inventory_items: Mapped[list[InventoryItem]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    meal_history: Mapped[list[MealHistory]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorite_recipes: Mapped[list[FavoriteRecipe]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1))
    current_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1))
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1))
    age: Mapped[int | None] = mapped_column(SmallInteger)
    gender: Mapped[str | None] = mapped_column(String(10))
    activity_level: Mapped[str | None] = mapped_column(String(20))
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer)
    fitness_goal: Mapped[str | None] = mapped_column(String(20))
    budget: Mapped[float | None] = mapped_column(Numeric(8, 2))
    meals_per_day: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=3
    )
    allergies: Mapped[str | None] = mapped_column(Text, default=None)
    favorite_foods: Mapped[str | None] = mapped_column(Text, default=None)
    disliked_foods: Mapped[str | None] = mapped_column(Text, default=None)

    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 150", name="chk_user_profiles_age"),
        CheckConstraint(
            "gender IN ('male', 'female', 'other')",
            name="chk_user_profiles_gender",
        ),
        CheckConstraint(
            "activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active')",
            name="chk_user_profiles_activity_level",
        ),
        CheckConstraint(
            "fitness_goal IN ('healthy', 'budget', 'high_protein', 'weight_loss', 'maintain')",
            name="chk_user_profiles_fitness_goal",
        ),
        CheckConstraint(
            "meals_per_day BETWEEN 1 AND 10",
            name="chk_user_profiles_meals_per_day",
        ),
        CheckConstraint(
            "budget IS NULL OR budget >= 0",
            name="chk_user_profiles_budget",
        ),
    )

    user: Mapped[User] = relationship(back_populates="profile")


class FoodPreference(CreatedAtMixin, Base):
    __tablename__ = "food_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    preference_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "preference_type IN ('liked', 'disliked')",
            name="chk_food_preferences_type",
        ),
        UniqueConstraint(
            "user_id", "ingredient_id", name="uq_food_preferences_user_ingredient"
        ),
    )

    user: Mapped[User] = relationship(back_populates="food_preferences")
    ingredient: Mapped[Ingredient] = relationship()


class DietaryRestriction(CreatedAtMixin, Base):
    __tablename__ = "dietary_restrictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    restriction: Mapped[str] = mapped_column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "restriction IN ('vegetarian', 'vegan', 'halal', 'keto', 'gluten_free', "
            "'paleo', 'mediterranean', 'low_carb', 'dairy_free', 'nut_free')",
            name="chk_dietary_restrictions_value",
        ),
    )

    user: Mapped[User] = relationship(back_populates="dietary_restrictions")


class UserAllergy(CreatedAtMixin, Base):
    __tablename__ = "user_allergies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    severity: Mapped[str | None] = mapped_column(String(20))

    __table_args__ = (
        UniqueConstraint(
            "user_id", "ingredient_id", name="uq_user_allergies"
        ),
        CheckConstraint(
            "severity IS NULL OR severity IN ('mild', 'moderate', 'severe')",
            name="chk_user_allergies_severity",
        ),
    )

    user: Mapped[User] = relationship(back_populates="allergies")
    ingredient: Mapped[Ingredient] = relationship()
