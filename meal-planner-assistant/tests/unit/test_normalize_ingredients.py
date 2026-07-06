import pytest
from app.tools.normalize_ingredients import normalize_ingredients, _parse_single_ingredient, _parse_fraction, _resolve_unit


class TestParseFraction:
    def test_simple_fraction(self):
        assert _parse_fraction("1/2") == 0.5

    def test_whole_fraction(self):
        assert _parse_fraction("3/4") == 0.75

    def test_mixed_fraction(self):
        assert _parse_fraction("1 1/2") == 1.5

    def test_integer_string(self):
        assert _parse_fraction("3") == 3.0

    def test_float_string(self):
        assert _parse_fraction("2.5") == 2.5

    def test_invalid_returns_one(self):
        assert _parse_fraction("abc") == 1.0

    def test_division_by_zero_returns_one(self):
        assert _parse_fraction("5/0") == 1.0


class TestResolveUnit:
    def test_grams(self):
        assert _resolve_unit("grams") == "g"
        assert _resolve_unit("gram") == "g"

    def test_kilograms(self):
        assert _resolve_unit("kg") == "kg"
        assert _resolve_unit("kilograms") == "kg"

    def test_milliliters(self):
        assert _resolve_unit("ml") == "ml"
        assert _resolve_unit("milliliters") == "ml"

    def test_liters(self):
        assert _resolve_unit("l") == "L"
        assert _resolve_unit("liters") == "L"

    def test_unknown_unit_passed_through(self):
        assert _resolve_unit("dashes") == "dashes"

    def test_period_stripped(self):
        assert _resolve_unit("g.") == "g"


class TestParseSingleIngredient:
    def test_quantity_unit_name(self):
        result = _parse_single_ingredient("200g chicken breast")
        assert result is not None
        assert result["name"] == "chicken breast"
        assert result["quantity"] == 200
        assert result["unit"] == "g"

    def test_quantity_space_unit_name(self):
        result = _parse_single_ingredient("2 cups rice")
        assert result is not None
        assert result["name"] == "rice"
        assert result["quantity"] == 2
        assert result["unit"] == "cup"

    def test_fractional_quantity(self):
        result = _parse_single_ingredient("1/2 cup milk")
        assert result is not None
        assert result["quantity"] == 0.5
        assert result["unit"] == "cup"

    def test_half_pattern(self):
        result = _parse_single_ingredient("half chicken breast")
        assert result is not None
        assert result["quantity"] == 0.5
        assert result["name"] == "chicken breast"

    def test_text_only_ingredient(self):
        result = _parse_single_ingredient("eggs")
        assert result is not None
        assert result["quantity"] == 1
        assert result["unit"] == "piece"
        assert result["name"] == "eggs"

    def test_empty_string(self):
        assert _parse_single_ingredient("") is None

    def test_whitespace_only(self):
        assert _parse_single_ingredient("   ") is None

    def test_name_normalization(self):
        result = _parse_single_ingredient("2 chicken breast")
        assert result["name"] == "chicken breast"

    def test_original_text_preserved(self):
        result = _parse_single_ingredient("3 eggs")
        assert result["original_text"] == "3 eggs"


class TestNormalizeIngredients:
    @pytest.mark.asyncio
    async def test_single_line(self):
        result = await normalize_ingredients("200g chicken breast")
        assert len(result) == 1
        assert result[0]["name"] == "chicken breast"

    @pytest.mark.asyncio
    async def test_multiple_lines(self):
        result = await normalize_ingredients("200g chicken breast\n3 eggs\n100ml milk")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_comma_separated(self):
        result = await normalize_ingredients("200g chicken breast, 3 eggs, 100ml milk")
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_semicolon_separated(self):
        result = await normalize_ingredients("200g chicken breast; 3 eggs")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_string(self):
        assert await normalize_ingredients("") == []

    @pytest.mark.asyncio
    async def test_blank_lines_skipped(self):
        result = await normalize_ingredients("200g chicken breast\n\n3 eggs\n\n")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_ingredient_normalization(self):
        result = await normalize_ingredients("200g breast")
        assert result[0]["name"] == "chicken breast"

    @pytest.mark.asyncio
    async def test_fraction_parsing(self):
        result = await normalize_ingredients("1/2 cup rice")
        assert result[0]["quantity"] == 0.5

    @pytest.mark.asyncio
    async def test_no_unit_defaults_to_piece(self):
        result = await normalize_ingredients("3 eggs")
        assert result[0]["unit"] == "piece"

    @pytest.mark.asyncio
    async def test_complex_fraction(self):
        result = await normalize_ingredients("1 1/2 cups flour")
        assert result[0]["quantity"] == 1.5
