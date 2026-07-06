
from mcp_servers.inventory_mcp.tools import (
    get_inventory,
    normalize_ingredient,
    save_inventory,
)


class TestSaveInventory:
    def test_save_and_get(self):
        ings = [{"name": "chicken breast", "quantity": 500, "unit": "g"}]
        result = save_inventory("user-1", ings)
        assert result["saved"] is True
        assert result["count"] == 1

        loaded = get_inventory("user-1")
        assert loaded["found"] is True
        assert loaded["ingredients"][0]["name"] == "chicken breast"

    def test_save_normalizes_names(self):
        ings = [{"name": "breast", "quantity": 300, "unit": "g"}]
        save_inventory("user-2", ings)
        loaded = get_inventory("user-2")
        assert loaded["ingredients"][0]["name"] == "chicken breast"

    def test_save_empty_list(self):
        result = save_inventory("user-3", [])
        assert result["saved"] is True
        assert result["count"] == 0

    def test_save_invalid_user_id(self):
        result = save_inventory("", [{"name": "eggs", "quantity": 6, "unit": "piece"}])
        assert result["saved"] is False

    def test_save_not_a_list(self):
        result = save_inventory("user-4", {})
        assert result["saved"] is False


class TestGetInventory:
    def test_get_nonexistent(self):
        result = get_inventory("no-such-user")
        assert result["found"] is False

    def test_get_empty_user_id(self):
        result = get_inventory("")
        assert result["found"] is False
        assert "error" in result


class TestNormalizeIngredient:
    def test_known_ingredient(self):
        result = normalize_ingredient("chicken breast")
        assert result["name"] == "chicken breast"
        assert result["known"] is True

    def test_alias_resolution(self):
        result = normalize_ingredient("breast")
        assert result["name"] == "chicken breast"
        assert result["known"] is True

    def test_unknown_ingredient(self):
        result = normalize_ingredient("unicorn meat")
        assert result["known"] is False

    def test_with_quantity_and_unit(self):
        result = normalize_ingredient("chicken breast", 200, "g")
        assert result["quantity"] == 200
        assert result["unit"] == "g"

    def test_unit_alias(self):
        result = normalize_ingredient("eggs", 3, "pieces")
        assert result["unit"] == "piece"

    def test_case_insensitive(self):
        result = normalize_ingredient("Chicken Breast")
        assert result["name"] == "chicken breast"

    def test_substring_match(self):
        result = normalize_ingredient("red bell pepper")
        assert result["name"] == "bell pepper"
