import pytest
from app.services.shopping_service import _build_available_map, _to_base_unit
from app.tools.shopping_list import generate_optimized_shopping_list


class TestBuildAvailableMap:
    def test_only_available_items(self):
        ingredients = [
            {"name": "chicken breast", "quantity": 500, "unit": "g", "available": True},
            {"name": "eggs", "quantity": 6, "unit": "piece", "available": False},
        ]
        result = _build_available_map(ingredients)
        assert "chicken breast" in result
        assert "eggs" not in result

    def test_empty_list(self):
        assert _build_available_map([]) == {}

    def test_case_insensitive(self):
        ingredients = [{"name": "CHICKEN BREAST", "quantity": 500, "unit": "g", "available": True}]
        result = _build_available_map(ingredients)
        assert "chicken breast" in result


class TestToBaseUnit:
    def test_g_stays_g(self):
        assert _to_base_unit(500, "g") == 500

    def test_kg_to_g(self):
        assert _to_base_unit(1, "kg") == 1000

    def test_l_to_ml(self):
        assert _to_base_unit(2, "L") == 2000

    def test_piece_stays(self):
        assert _to_base_unit(3, "piece") == 3


class TestGenerateOptimizedShoppingList:
    @pytest.mark.asyncio
    async def test_single_recipe_no_available(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "chicken breast", "quantity": 200, "unit": "g"},
                    {"name": "lettuce", "quantity": 100, "unit": "g"},
                ]
            }
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert len(result) == 2
        names = {item["ingredient_name"] for item in result}
        assert "chicken breast" in names
        assert "lettuce" in names

    @pytest.mark.asyncio
    async def test_deduct_available_ingredients(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "chicken breast", "quantity": 500, "unit": "g"},
                ]
            }
        ]
        available = [{"name": "chicken breast", "quantity": 300, "unit": "g", "available": True}]
        result = await generate_optimized_shopping_list(recipes, available)
        assert len(result) == 1
        assert result[0]["total_quantity"] == 200

    @pytest.mark.asyncio
    async def test_available_exceeds_needed(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "chicken breast", "quantity": 200, "unit": "g"},
                ]
            }
        ]
        available = [{"name": "chicken breast", "quantity": 500, "unit": "g", "available": True}]
        result = await generate_optimized_shopping_list(recipes, available)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_merge_duplicate_across_recipes(self):
        recipes = [
            {"ingredients": [{"name": "chicken breast", "quantity": 200, "unit": "g"}]},
            {"ingredients": [{"name": "chicken breast", "quantity": 300, "unit": "g"}]},
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert len(result) == 1
        assert result[0]["total_quantity"] == 500

    @pytest.mark.asyncio
    async def test_unknown_ingredient_in_result(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "truffle oil", "quantity": 100, "unit": "ml"},
                ]
            }
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert len(result) == 1
        assert result[0]["category"] == "unknown"

    @pytest.mark.asyncio
    async def test_mixed_units_same_ingredient(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "milk", "quantity": 1, "unit": "L"},
                    {"name": "milk", "quantity": 500, "unit": "ml"},
                ]
            }
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_recipes(self):
        result = await generate_optimized_shopping_list([], [])
        assert result == []

    @pytest.mark.asyncio
    async def test_recipe_missing_ingredients_key(self):
        result = await generate_optimized_shopping_list([{"name": "no ingredients here"}], [])
        assert result == []

    @pytest.mark.asyncio
    async def test_estimated_cost_calculated(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "chicken breast", "quantity": 1, "unit": "kg"},
                ]
            }
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert result[0]["estimated_cost"] == pytest.approx(8.99, rel=0.01)

    @pytest.mark.asyncio
    async def test_category_from_price_db(self):
        recipes = [
            {
                "ingredients": [
                    {"name": "eggs", "quantity": 12, "unit": "piece"},
                ]
            }
        ]
        result = await generate_optimized_shopping_list(recipes, [])
        assert result[0]["category"] == "dairy"
