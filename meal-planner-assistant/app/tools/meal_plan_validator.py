from app.services.meal_plan_service import MealPlanService


def validate_meal_plan(
    meal_plan: list[dict],
    daily_calorie_target: float,
    daily_protein_target: float = 0,
    daily_carbs_target: float = 0,
    daily_fat_target: float = 0,
) -> dict:
    service = MealPlanService()
    return service.validate(
        meal_plan,
        daily_calorie_target,
        daily_protein_target,
        daily_carbs_target,
        daily_fat_target,
    )
