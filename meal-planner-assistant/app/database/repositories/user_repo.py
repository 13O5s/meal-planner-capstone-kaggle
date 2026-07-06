from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import (
    DietaryRestriction,
    FoodPreference,
    User,
    UserAllergy,
    UserProfile,
)
from app.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> User | None:
        return await self.find_one(email=email)

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_profile(
        self, user_id: uuid.UUID, **kwargs
    ) -> UserProfile:
        existing = await self.get_profile(user_id)
        if existing:
            for key, val in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, val)
            await self._session.flush()
            return existing
        profile = UserProfile(user_id=user_id, **kwargs)
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_preferences(
        self, user_id: uuid.UUID
    ) -> Sequence[FoodPreference]:
        result = await self._session.execute(
            select(FoodPreference).where(
                FoodPreference.user_id == user_id
            )
        )
        return result.scalars().all()

    async def add_preference(
        self, user_id: uuid.UUID, ingredient_id: uuid.UUID, pref_type: str
    ) -> FoodPreference:
        fp = FoodPreference(
            user_id=user_id,
            ingredient_id=ingredient_id,
            preference_type=pref_type,
        )
        self._session.add(fp)
        await self._session.flush()
        return fp

    async def get_dietary_restrictions(
        self, user_id: uuid.UUID
    ) -> Sequence[DietaryRestriction]:
        result = await self._session.execute(
            select(DietaryRestriction).where(
                DietaryRestriction.user_id == user_id
            )
        )
        return result.scalars().all()

    async def get_allergies(
        self, user_id: uuid.UUID
    ) -> Sequence[UserAllergy]:
        result = await self._session.execute(
            select(UserAllergy).where(
                UserAllergy.user_id == user_id
            )
        )
        return result.scalars().all()
