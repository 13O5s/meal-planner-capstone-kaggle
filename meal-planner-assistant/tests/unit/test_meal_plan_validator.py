from app.tools.meal_plan_validator import validate_meal_plan


class TestValidateMealPlan:
    def test_valid_single_day(self):
        plan = [
            {
                "day": "Monday",
                "meals": ["Grilled Chicken Salad"],
                "total_nutrition": {"calories": 2000, "protein": 150, "carbohydrates": 200, "fat": 55},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert result["valid"] is True
        assert result["day_results"][0]["valid"] is True
        assert "meets" not in result  # not a nested key issue

    def test_calories_within_tolerance(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 1900, "protein": 0, "carbohydrates": 0, "fat": 0},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert result["valid"] is True

    def test_calories_outside_tolerance(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 1500, "protein": 0, "carbohydrates": 0, "fat": 0},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert result["valid"] is False

    def test_protein_target_provided(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 150, "carbohydrates": 200, "fat": 55},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000, daily_protein_target=150)
        assert result["valid"] is True

    def test_protein_out_of_range(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 50, "carbohydrates": 200, "fat": 55},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000, daily_protein_target=150)
        assert result["valid"] is False

    def test_all_macros_valid(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 150, "carbohydrates": 200, "fat": 55},
            }
        ]
        result = validate_meal_plan(
            plan,
            daily_calorie_target=2000,
            daily_protein_target=150,
            daily_carbs_target=200,
            daily_fat_target=55,
        )
        assert result["valid"] is True

    def test_one_macro_fails(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 150, "carbohydrates": 300, "fat": 55},
            }
        ]
        result = validate_meal_plan(
            plan,
            daily_calorie_target=2000,
            daily_protein_target=150,
            daily_carbs_target=200,
            daily_fat_target=55,
        )
        assert result["valid"] is False

    def test_multiple_days(self, sample_meal_plan):
        result = validate_meal_plan(sample_meal_plan, daily_calorie_target=2000)
        assert "day_results" in result
        assert len(result["day_results"]) == 2

    def test_summary_all_valid(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 0, "carbohydrates": 0, "fat": 0},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert "meet nutritional targets" in result["summary"]

    def test_summary_some_invalid(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 500, "protein": 0, "carbohydrates": 0, "fat": 0},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert "do not meet" in result["summary"]

    def test_optional_macros_default_to_ok(self):
        plan = [
            {
                "day": "Monday",
                "meals": [],
                "total_nutrition": {"calories": 2000, "protein": 999, "carbohydrates": 999, "fat": 999},
            }
        ]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert result["valid"] is True

    def test_empty_meal_plan(self):
        result = validate_meal_plan([], daily_calorie_target=2000)
        assert result["valid"] is True
        assert result["day_results"] == []

    def test_missing_total_nutrition(self):
        plan = [{"day": "Monday", "meals": ["Grilled Chicken Salad"]}]
        result = validate_meal_plan(plan, daily_calorie_target=2000)
        assert result["valid"] is False
