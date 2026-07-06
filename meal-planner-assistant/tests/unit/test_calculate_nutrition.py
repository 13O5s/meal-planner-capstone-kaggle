import pytest
from app.tools.calculate_nutrition import calculate_recipe_nutrition


class TestCalculateNutrition:
    @pytest.mark.asyncio
    async def test_single_known_ingredient_by_weight(self):
        result = await calculate_recipe_nutrition([{"name": "chicken breast", "quantity": 200, "unit": "g"}])
        assert result["calories"] == pytest.approx(330, rel=0.01)
        assert result["protein"] == pytest.approx(62, rel=0.01)
        assert result["carbohydrates"] == 0
        assert result["fat"] == pytest.approx(7.2, rel=0.01)

    @pytest.mark.asyncio
    async def test_single_ingredient_by_piece(self):
        result = await calculate_recipe_nutrition([{"name": "eggs", "quantity": 3, "unit": "piece"}])
        assert result["calories"] == pytest.approx(210, rel=0.01)
        assert result["protein"] == pytest.approx(18, rel=0.01)

    @pytest.mark.asyncio
    async def test_single_ingredient_by_volume(self):
        result = await calculate_recipe_nutrition([{"name": "olive oil", "quantity": 50, "unit": "ml"}])
        assert result["calories"] == pytest.approx(442, rel=0.01)
        assert result["fat"] == pytest.approx(50, rel=0.01)

    @pytest.mark.asyncio
    async def test_multiple_ingredients(self, sample_ingredients):
        result = await calculate_recipe_nutrition(sample_ingredients)
        assert result["calories"] > 0
        assert result["protein"] > 0
        assert result["carbohydrates"] >= 0
        assert result["fat"] > 0

    @pytest.mark.asyncio
    async def test_unknown_ingredient_skipped(self):
        result = await calculate_recipe_nutrition([{"name": "unknown_ingredient_x", "quantity": 100, "unit": "g"}])
        assert result == {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}

    @pytest.mark.asyncio
    async def test_mixed_known_and_unknown(self):
        result = await calculate_recipe_nutrition([
            {"name": "chicken breast", "quantity": 100, "unit": "g"},
            {"name": "dragon fruit", "quantity": 200, "unit": "g"},
        ])
        assert result["calories"] == pytest.approx(165, rel=0.01)

    @pytest.mark.asyncio
    async def test_empty_list(self):
        result = await calculate_recipe_nutrition([])
        assert result == {"calories": 0, "protein": 0, "carbohydrates": 0, "fat": 0}

    @pytest.mark.asyncio
    async def test_quantity_in_kg(self):
        result = await calculate_recipe_nutrition([{"name": "chicken breast", "quantity": 0.5, "unit": "kg"}])
        assert result["calories"] == pytest.approx(825, rel=0.01)

    @pytest.mark.asyncio
    async def test_quantity_in_liters(self):
        result = await calculate_recipe_nutrition([{"name": "milk", "quantity": 1, "unit": "L"}])
        assert result["calories"] == pytest.approx(420, rel=0.01)
        assert result["protein"] == pytest.approx(34, rel=0.01)

    @pytest.mark.asyncio
    async def test_case_insensitive_name(self):
        result = await calculate_recipe_nutrition([{"name": "CHICKEN BREAST", "quantity": 200, "unit": "g"}])
        assert result["calories"] == pytest.approx(330, rel=0.01)

    @pytest.mark.asyncio
    async def test_missing_keys_defaults(self):
        result = await calculate_recipe_nutrition([{"name": "chicken breast"}])
        assert result["calories"] == 0

    @pytest.mark.asyncio
    async def test_recipe_from_stores(self, sample_recipe_ingredients):
        result = await calculate_recipe_nutrition(sample_recipe_ingredients)
        assert result["calories"] > 0
        assert result["protein"] > 0

    @pytest.mark.asyncio
    async def test_milk_by_ml(self):
        result = await calculate_recipe_nutrition([{"name": "milk", "quantity": 250, "unit": "ml"}])
        assert result["calories"] == pytest.approx(105, rel=0.01)
