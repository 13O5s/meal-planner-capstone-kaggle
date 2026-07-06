import time

_PROFILE_DB: dict[str, dict] = {}
_VALID_GOALS = {"healthy", "budget", "high_protein", "weight_loss"}
_VALID_ACTIVITY_LEVELS = {"sedentary", "light", "moderate", "active", "very_active"}
_VALID_GENDERS = {"male", "female", "other"}


def save_profile(user_id: str, profile_data: dict) -> dict:
    if not user_id or not isinstance(profile_data, dict):
        return {"saved": False, "error": "user_id and profile_data are required"}
    _PROFILE_DB[user_id] = dict(profile_data)
    return {"saved": True, "user_id": user_id, "timestamp": time.time()}


def get_profile(user_id: str) -> dict:
    if not user_id:
        return {"found": False, "error": "user_id is required"}
    profile = _PROFILE_DB.get(user_id)
    if profile is None:
        return {"found": False, "user_id": user_id}
    return {"found": True, "user_id": user_id, "profile": dict(profile)}


def validate_profile(profile_data: dict) -> dict:
    errors = []
    if "age" in profile_data:
        age = profile_data["age"]
        if not isinstance(age, int) or age < 1 or age > 150:
            errors.append("age must be an integer between 1 and 150")

    if "goal" in profile_data and profile_data["goal"] not in _VALID_GOALS:
        errors.append(f"goal must be one of {sorted(_VALID_GOALS)}")

    if "activity_level" in profile_data and profile_data["activity_level"] not in _VALID_ACTIVITY_LEVELS:
        errors.append(f"activity_level must be one of {sorted(_VALID_ACTIVITY_LEVELS)}")

    if "gender" in profile_data and profile_data["gender"] not in _VALID_GENDERS:
        errors.append(f"gender must be one of {sorted(_VALID_GENDERS)}")

    if "height_cm" in profile_data:
        h = profile_data["height_cm"]
        if not isinstance(h, (int, float)) or h < 50 or h > 300:
            errors.append("height_cm must be between 50 and 300")

    if "weight_kg" in profile_data:
        w = profile_data["weight_kg"]
        if not isinstance(w, (int, float)) or w < 10 or w > 600:
            errors.append("weight_kg must be between 10 and 600")

    return {"valid": len(errors) == 0, "errors": errors}
