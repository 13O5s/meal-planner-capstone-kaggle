from app.services.helper import optional_session
from app.services.profile_service import ProfileService


async def save_profile(profile_data: dict) -> dict:
    missing = ProfileService.validate_required(ProfileService(None), profile_data)
    if missing:
        return {
            "success": False,
            "error": f"Missing required fields: {', '.join(missing)}",
            "missing_fields": missing,
        }

    async with optional_session() as session:
        service = ProfileService(session)
        return await service.save_profile(profile_data)
