class MealPlanService:
    def validate(
        self,
        meal_plan: list[dict],
        daily_calorie_target: float,
        daily_protein_target: float = 0,
        daily_carbs_target: float = 0,
        daily_fat_target: float = 0,
    ) -> dict:
        tolerance = 0.10
        day_results = []
        all_valid = True

        for day in meal_plan:
            nutrition = day.get("total_nutrition", {})
            day_cal = nutrition.get("calories", 0)
            day_protein = nutrition.get("protein", 0)
            day_carbs = nutrition.get("carbohydrates", 0)
            day_fat = nutrition.get("fat", 0)

            cal_lower = daily_calorie_target * (1 - tolerance)
            cal_upper = daily_calorie_target * (1 + tolerance)
            cal_ok = cal_lower <= day_cal <= cal_upper

            protein_ok = True
            if daily_protein_target > 0:
                p_lower = daily_protein_target * (1 - tolerance)
                p_upper = daily_protein_target * (1 + tolerance)
                protein_ok = p_lower <= day_protein <= p_upper

            carbs_ok = True
            if daily_carbs_target > 0:
                c_lower = daily_carbs_target * (1 - tolerance)
                c_upper = daily_carbs_target * (1 + tolerance)
                carbs_ok = c_lower <= day_carbs <= c_upper

            fat_ok = True
            if daily_fat_target > 0:
                f_lower = daily_fat_target * (1 - tolerance)
                f_upper = daily_fat_target * (1 + tolerance)
                fat_ok = f_lower <= day_fat <= f_upper

            day_valid = cal_ok and protein_ok and carbs_ok and fat_ok
            if not day_valid:
                all_valid = False

            day_results.append(
                {
                    "day": day.get("day", ""),
                    "valid": day_valid,
                    "details": {
                        "calories": {
                            "target": daily_calorie_target,
                            "actual": day_cal,
                            "meets": cal_ok,
                        },
                        "protein": {
                            "target": daily_protein_target,
                            "actual": day_protein,
                            "meets": protein_ok,
                        },
                        "carbohydrates": {
                            "target": daily_carbs_target,
                            "actual": day_carbs,
                            "meets": carbs_ok,
                        },
                        "fat": {
                            "target": daily_fat_target,
                            "actual": day_fat,
                            "meets": fat_ok,
                        },
                    },
                }
            )

        return {
            "valid": all_valid,
            "day_results": day_results,
            "summary": "All days meet nutritional targets."
            if all_valid
            else "Some days do not meet nutritional targets.",
        }
