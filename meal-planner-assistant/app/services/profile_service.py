import json
import uuid
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import DietaryRestriction
from app.database.repositories import IngredientRepository, UserRepository

_ACTIVITY_MAP = {
    "Sedentary": "sedentary",
    "Light": "light",
    "Moderate": "moderate",
    "Active": "active",
    "Very Active": "very_active",
}

_GOAL_MAP = {
    "Weight Loss": "weight_loss",
    "Weight Gain": "maintain",
    "Maintain Muscle": "maintain",
    "General Health": "healthy",
    "High Protein": "high_protein",
}


class ProfileService:
    REQUIRED_FIELDS: ClassVar[list[str]] = [
        "age",
        "gender",
        "height_cm",
        "weight_kg",
        "activity_level",
        "budget",
        "goal",
        "meals_per_day",
    ]

    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session
        self._user_repo = UserRepository(session) if session else None
        self._ingredient_repo = IngredientRepository(session) if session else None
        self._guest_user_id: uuid.UUID | None = None

    def validate_required(self, data: dict) -> list[str]:
        missing = []
        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None or data[field] == "":
                missing.append(field)
        return missing

    async def save_profile(self, data: dict) -> dict:
        if self._user_repo:
            return await self._save_to_db(data)
        return self._save_in_memory(data)

    async def get_profile(self, user_id: str | None = None) -> dict | None:
        if self._user_repo:
            return await self._get_from_db(user_id)
        return None

    async def _save_to_db(self, data: dict) -> dict:
        raw_uid = data.get("user_id")
        if raw_uid:
            uid = uuid.UUID(raw_uid)
            user = await self._user_repo.get(uid)
        if not raw_uid or user is None:
            user_email = data.get("email", "guest@meal-planner.local")
            user = await self._user_repo.find_by_email(user_email)
        if user is None:
            user = await self._user_repo.create(
                email=user_email or "guest@meal-planner.local",
                password_hash="",
            )

        raw_activity = data.get("activity_level")
        mapped_activity = _ACTIVITY_MAP.get(raw_activity, raw_activity)

        raw_goal = data.get("goal")
        mapped_goal = _GOAL_MAP.get(raw_goal, raw_goal)

        profile_data = {
            "age": data.get("age"),
            "gender": data.get("gender"),
            "height_cm": data.get("height_cm"),
            "current_weight_kg": data.get("weight_kg"),
            "target_weight_kg": data.get("target_weight_kg"),
            "activity_level": mapped_activity,
            "daily_calorie_target": data.get("daily_calorie_target"),
            "fitness_goal": mapped_goal,
            "budget": data.get("budget"),
            "meals_per_day": data.get("meals_per_day", 3),
            "allergies": json.dumps(data.get("allergies", []), ensure_ascii=False),
            "favorite_foods": json.dumps(data.get("favorite_foods", []), ensure_ascii=False),
            "disliked_foods": json.dumps(data.get("disliked_foods", []), ensure_ascii=False),
        }
        await self._user_repo.upsert_profile(user.id, **profile_data)

        if "favorite_foods" in data and self._ingredient_repo:
            for fav in data["favorite_foods"]:
                ing = await self._ingredient_repo.resolve_name(fav)
                if ing:
                    existing = await self._user_repo.get_preferences(user.id)
                    if not any(
                        e.ingredient_id == ing.id and e.preference_type == "liked"
                        for e in existing
                    ):
                        await self._user_repo.add_preference(
                            user.id, ing.id, "liked"
                        )

        if "disliked_foods" in data and self._ingredient_repo:
            for dis in data["disliked_foods"]:
                ing = await self._ingredient_repo.resolve_name(dis)
                if ing:
                    existing = await self._user_repo.get_preferences(user.id)
                    if not any(
                        e.ingredient_id == ing.id and e.preference_type == "disliked"
                        for e in existing
                    ):
                        await self._user_repo.add_preference(
                            user.id, ing.id, "disliked"
                        )

        if "dietary_preferences" in data and self._user_repo:
            existing_restrictions = {
                r.restriction
                for r in await self._user_repo.get_dietary_restrictions(user.id)
            }
            for pref in data["dietary_preferences"]:
                if pref not in existing_restrictions:
                    dr = DietaryRestriction(user_id=user.id, restriction=pref)
                    self._user_repo._session.add(dr)

        self._guest_user_id = user.id
        await self._user_repo._session.flush()

        return {
            "success": True,
            "user_id": str(user.id),
            "fields_saved": list(profile_data.keys()),
        }

    def _save_in_memory(self, data: dict) -> dict:
        self._guest_user_id = uuid.uuid4()
        return {
            "success": True,
            "user_id": str(self._guest_user_id),
            "fields_saved": list(data.keys()),
            "note": "Saved in-memory (no database connected)",
        }

    async def _get_from_db(self, user_id: str | None) -> dict | None:
        uid = uuid.UUID(user_id) if user_id else self._guest_user_id
        if uid is None:
            return None
        user = await self._user_repo.get(uid)
        if user is None:
            return None
        profile = await self._user_repo.get_profile(user.id)
        if profile is None:
            return None

        def _parse_json(val: str | None) -> list:
            if not val:
                return []
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return []

        restrictions = await self._user_repo.get_dietary_restrictions(user.id)

        return {
            "age": profile.age,
            "gender": profile.gender,
            "height_cm": float(profile.height_cm) if profile.height_cm else None,
            "weight_kg": float(profile.current_weight_kg) if profile.current_weight_kg else None,
            "target_weight_kg": float(profile.target_weight_kg) if profile.target_weight_kg else None,
            "activity_level": profile.activity_level,
            "daily_calorie_target": profile.daily_calorie_target,
            "goal": profile.fitness_goal,
            "budget": float(profile.budget) if profile.budget else None,
            "meals_per_day": profile.meals_per_day,
            "allergies": _parse_json(profile.allergies),
            "favorite_foods": _parse_json(profile.favorite_foods),
            "disliked_foods": _parse_json(profile.disliked_foods),
            "dietary_preferences": [r.restriction for r in restrictions],
        }
