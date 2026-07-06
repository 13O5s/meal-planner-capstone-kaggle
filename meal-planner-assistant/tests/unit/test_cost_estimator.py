import pytest

from app.tools.cost_estimator import _calculate_cost, estimate_grocery_cost


class TestCalculateCost:
    def test_same_unit(self):
        cost = _calculate_cost(2, "piece", 1.50, "piece")
        assert cost == 3.0

    def test_kg_to_g(self):
        cost = _calculate_cost(500, "g", 8.99, "kg")
        assert cost == pytest.approx(8.99 * 0.5, rel=0.01)

    def test_kg_to_kg(self):
        cost = _calculate_cost(2, "kg", 5.00, "kg")
        assert cost == 10.0

    def test_l_to_ml(self):
        cost = _calculate_cost(250, "ml", 8.00, "L")
        assert cost == pytest.approx(8.00 * 0.25, rel=0.01)

    def test_l_to_l(self):
        cost = _calculate_cost(3, "L", 2.00, "L")
        assert cost == 6.0

    def test_piece_to_kg_fallback(self):
        cost = _calculate_cost(5, "piece", 10.00, "kg")
        assert cost == pytest.approx(10.0 * (5 * 0.2), rel=0.01)

    def test_unknown_unit_fallback(self):
        cost = _calculate_cost(3, "handful", 2.00, "kg")
        assert cost == 6.0


class TestEstimateGroceryCost:
    @pytest.mark.asyncio
    async def test_single_known_ingredient(self):
        result = await estimate_grocery_cost([{"name": "chicken breast", "quantity": 1, "unit": "kg"}])
        assert result["total_cost"] == pytest.approx(8.99, rel=0.01)
        assert len(result["itemized_costs"]) == 1
        assert len(result["unknown_ingredients"]) == 0

    @pytest.mark.asyncio
    async def test_unknown_ingredient_flagged(self):
        result = await estimate_grocery_cost([{"name": "truffle oil", "quantity": 100, "unit": "ml"}])
        assert result["total_cost"] == 0
        assert len(result["itemized_costs"]) == 0
        assert len(result["unknown_ingredients"]) == 1
        assert result["unknown_ingredients"][0]["name"] == "truffle oil"

    @pytest.mark.asyncio
    async def test_mixed_known_and_unknown(self):
        result = await estimate_grocery_cost([
            {"name": "chicken breast", "quantity": 500, "unit": "g"},
            {"name": "dragon fruit", "quantity": 2, "unit": "piece"},
        ])
        assert result["total_cost"] == pytest.approx(8.99 * 0.5, rel=0.01)
        assert len(result["itemized_costs"]) == 1
        assert len(result["unknown_ingredients"]) == 1

    @pytest.mark.asyncio
    async def test_multiple_ingredients(self):
        result = await estimate_grocery_cost([
            {"name": "chicken breast", "quantity": 1, "unit": "kg"},
            {"name": "eggs", "quantity": 12, "unit": "piece"},
            {"name": "milk", "quantity": 2, "unit": "L"},
        ])
        expected = 8.99 + (12 * 0.35) + (2 * 1.50)
        assert result["total_cost"] == pytest.approx(expected, rel=0.01)
        assert len(result["itemized_costs"]) == 3

    @pytest.mark.asyncio
    async def test_empty_list(self):
        result = await estimate_grocery_cost([])
        assert result["total_cost"] == 0
        assert result["itemized_costs"] == []
        assert result["unknown_ingredients"] == []

    @pytest.mark.asyncio
    async def test_currency_is_usd(self):
        result = await estimate_grocery_cost([{"name": "eggs", "quantity": 6, "unit": "piece"}])
        assert result["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_itemized_has_category(self):
        result = await estimate_grocery_cost([{"name": "chicken breast", "quantity": 1, "unit": "kg"}])
        item = result["itemized_costs"][0]
        assert item["category"] == "meat"
        assert item["name"] == "chicken breast"

    @pytest.mark.asyncio
    async def test_case_insensitive_name(self):
        result = await estimate_grocery_cost([{"name": "CHICKEN BREAST", "quantity": 1, "unit": "kg"}])
        assert result["total_cost"] == pytest.approx(8.99, rel=0.01)
