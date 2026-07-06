import pytest

from mcp_servers.profile_mcp.tools import get_profile, save_profile, validate_profile


class TestSaveProfile:
    def test_save_and_get(self):
        result = save_profile("user-1", {"age": 30, "goal": "healthy"})
        assert result["saved"] is True
        assert result["user_id"] == "user-1"

        loaded = get_profile("user-1")
        assert loaded["found"] is True
        assert loaded["profile"]["age"] == 30

    def test_save_empty_user_id(self):
        result = save_profile("", {"age": 30})
        assert result["saved"] is False

    def test_save_none_data(self):
        result = save_profile("user-2", {})
        assert result["saved"] is True

    def test_update_existing(self):
        save_profile("user-3", {"age": 25})
        save_profile("user-3", {"age": 26, "goal": "weight_loss"})
        loaded = get_profile("user-3")
        assert loaded["profile"]["age"] == 26
        assert loaded["profile"]["goal"] == "weight_loss"


class TestGetProfile:
    def test_get_nonexistent(self):
        result = get_profile("no-such-user")
        assert result["found"] is False

    def test_get_empty_user_id(self):
        result = get_profile("")
        assert result["found"] is False
        assert "error" in result


class TestValidateProfile:
    def test_valid_profile(self):
        result = validate_profile({
            "age": 30,
            "gender": "male",
            "height_cm": 175,
            "weight_kg": 70,
            "goal": "healthy",
        })
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_age_too_high(self):
        result = validate_profile({"age": 999})
        assert result["valid"] is False
        assert any("age" in e for e in result["errors"])

    def test_invalid_age_string(self):
        result = validate_profile({"age": "thirty"})
        assert result["valid"] is False

    def test_invalid_goal(self):
        result = validate_profile({"goal": "extreme_loss"})
        assert result["valid"] is False
        assert any("goal" in e for e in result["errors"])

    def test_invalid_activity_level(self):
        result = validate_profile({"activity_level": "super_active"})
        assert result["valid"] is False

    def test_invalid_gender(self):
        result = validate_profile({"gender": "alien"})
        assert result["valid"] is False

    def test_invalid_height(self):
        result = validate_profile({"height_cm": 999})
        assert result["valid"] is False

    def test_invalid_weight(self):
        result = validate_profile({"weight_kg": -5})
        assert result["valid"] is False

    def test_empty_profile(self):
        result = validate_profile({})
        assert result["valid"] is True
        assert result["errors"] == []
