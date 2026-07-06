import os
import re
from dataclasses import dataclass, field
from typing import Any

from app.data.stores import NUTRITION_DB, PRICE_DB, normalize_ingredient_name
from app.tools.normalize_ingredients import UNIT_ALIASES

_SECURE_LOGGING = os.environ.get("SECURITY_CHECKPOINT_LOGGING", "0") == "1"


@dataclass
class SecurityEvent:
    category: str
    severity: str
    field: str | None
    detail: str
    sanitized: bool = False


@dataclass
class SecurityCheckpointResult:
    passed: bool = True
    blocked: bool = False
    events: list[SecurityEvent] = field(default_factory=list)
    sanitized_data: dict[str, Any] | None = None
    validation_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex patterns for PII detection
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    (
        "email",
        "medium",
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    ),
    (
        "credit_card",
        "high",
        re.compile(
            r"\b(?:\d[ -]*?){13,16}\b",
        ),
    ),
    (
        "api_key",
        "high",
        re.compile(
            r"(?i)(?:api[_-]?key|apikey|secret|token)\s*[:=]\s*['\"]?[\w-]{16,}",
        ),
    ),
    (
        "access_token",
        "high",
        re.compile(
            r"(?i)(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}",
        ),
    ),
    (
        "phone",
        "medium",
        re.compile(
            r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
        ),
    ),
    (
        "government_id",
        "high",
        re.compile(
            r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
        ),
    ),
]

# ---------------------------------------------------------------------------
# Prompt-injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[tuple[str, re.Pattern]] = [
    (
        "ignore_system",
        re.compile(
            r"(?i)(?:ignore|override|disregard)\s+(?:all\s+)?(?:system|previous|your)\s+(?:instructions|directives|rules|prompt)",
        ),
    ),
    (
        "ignore_allergies",
        re.compile(
            r"(?i)(?:ignore|bypass|skip|disable)\s+(?:my\s+)?(?:allergies|allergy|dietary\s+restrictions|diet)",
        ),
    ),
    (
        "reveal_prompt",
        re.compile(
            r"(?i)(?:reveal|show|print|output|display|tell\s+me)\s+(?:me\s+)?(?:your\s+)?(?:prompt|instructions|system\s+prompt|system\s+instructions)",
        ),
    ),
    (
        "reveal_secrets",
        re.compile(
            r"(?i)(?:reveal|show|leak|expose|give\s+me|tell\s+me)\s+(?:the\s+)?(?:api\s*key|secret|token|password|credentials)",
        ),
    ),
    (
        "bypass_validation",
        re.compile(
            r"(?i)(?:bypass|skip|disable|turn\s+off)\s+(?:all\s+)?(?:validation|security|safety|checks|filters)",
        ),
    ),
    (
        "new_identity",
        re.compile(
            r"(?i)(?:you\s+are\s+now|act\s+as\s+if|pretend\s+(?:to\s+be|that)|from\s+now\s+on\s+you\s+are)\s+.+",
        ),
    ),
    (
        "forget_previous",
        re.compile(
            r"(?i)(?:forget|ignore|discard|erase|clear)\s+(?:all\s+)?(?:previous|earlier|past)\s+(?:instructions|context|conversation|history)",
        ),
    ),
]

# ---------------------------------------------------------------------------
# Supported values for constrained fields
# ---------------------------------------------------------------------------

_VALID_GOALS = {"healthy", "budget", "high_protein", "weight_loss"}
_VALID_ACTIVITY_LEVELS = {
    "sedentary",
    "light",
    "moderate",
    "active",
    "very_active",
}
_VALID_GENDERS = {"male", "female", "other"}
_VALID_PLANNING_MODES = {"daily", "weekly"}
_VALID_DIETARY_PREFERENCES = {
    "vegetarian",
    "vegan",
    "keto",
    "gluten_free",
    "gluten-free",
    "paleo",
    "mediterranean",
    "low_carb",
    "low_fat",
}
_KNOWN_INGREDIENTS: set[str] = set(NUTRITION_DB.keys()) | set(PRICE_DB.keys())
_CALORIE_MIN = 500
_CALORIE_MAX = 10_000
_BUDGET_MAX = 10_000.0
_AGE_MIN = 1
_AGE_MAX = 150
_HEIGHT_MIN_CM = 50.0
_HEIGHT_MAX_CM = 300.0
_WEIGHT_MIN_KG = 10.0
_WEIGHT_MAX_KG = 600.0
_MEALS_PER_DAY_MIN = 1
_MEALS_PER_DAY_MAX = 8
_MACRO_TOLERANCE = 0.10


def _log(level: str, message: str) -> None:
    if _SECURE_LOGGING:
        print(f"[security_checkpoint] {level}: {message}")


# ===================================================================
# 1. Input validation
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Validates raw input structure of the user profile and available ingredients.
# - Prevents malformed, out-of-range, or incorrect data types from proceeding downstream.
#
# HOW IT WORKS:
# - Step 1: Extracts `user_profile` from the session state dict and verifies it is a dictionary.
# - Step 2: Uses helper function `_validate_profile_field` to check numeric fields like age, height,
#   weight, calorie target, budget, and meals per day, enforcing types and min/max constraints.
# - Step 3: Compares `goal`, `activity_level`, and `gender` against predefined valid sets (enums).
# - Step 4: Iterates through the list of `available_ingredients`. Ensures each item is a dict with
#   required keys: 'name', 'quantity', and 'unit'.
# - Step 5: Checks that ingredient quantity is numeric and non-negative.
# - If any check fails, it logs validation errors, creates a "block" severity SecurityEvent,
#   and flags `passed = False` and `blocked = True`.
# ===================================================================
def validate_input(data: dict[str, Any]) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()

    profile = data.get("user_profile", {})
    if not isinstance(profile, dict):
        result.validation_errors.append("user_profile must be a dict")
        result.passed = False
        result.blocked = True
        return result

    _validate_profile_field(profile, "age", int, _AGE_MIN, _AGE_MAX, result)
    _validate_profile_field(
        profile, "height_cm", (int, float), _HEIGHT_MIN_CM, _HEIGHT_MAX_CM, result
    )
    _validate_profile_field(
        profile, "weight_kg", (int, float), _WEIGHT_MIN_KG, _WEIGHT_MAX_KG, result
    )
    _validate_profile_field(
        profile,
        "daily_calorie_target",
        (int, float),
        _CALORIE_MIN,
        _CALORIE_MAX,
        result,
        optional=True,
    )
    _validate_profile_field(
        profile,
        "budget",
        (int, float),
        0,
        _BUDGET_MAX,
        result,
        optional=True,
    )
    _validate_profile_field(
        profile,
        "meals_per_day",
        int,
        _MEALS_PER_DAY_MIN,
        _MEALS_PER_DAY_MAX,
        result,
        optional=True,
    )

    if "goal" in profile and profile["goal"] not in _VALID_GOALS:
        _reject(result, "goal", f"Unsupported goal: {profile['goal']}")

    if (
        "activity_level" in profile
        and profile["activity_level"] not in _VALID_ACTIVITY_LEVELS
    ):
        _reject(
            result,
            "activity_level",
            f"Unsupported activity_level: {profile['activity_level']}",
        )

    if "gender" in profile and profile["gender"] not in _VALID_GENDERS:
        _reject(result, "gender", f"Unsupported gender: {profile['gender']}")

    inventory = data.get("available_ingredients", [])
    if not isinstance(inventory, list):
        _reject(result, "available_ingredients", "Must be a list")
    else:
        for i, ing in enumerate(inventory):
            if not isinstance(ing, dict):
                _reject(
                    result,
                    f"available_ingredients[{i}]",
                    "Each ingredient must be a dict",
                )
            elif not all(k in ing for k in ("name", "quantity", "unit")):
                _reject(
                    result,
                    f"available_ingredients[{i}]",
                    f"Missing required keys (name, quantity, unit): {ing}",
                )
            else:
                qty = ing.get("quantity", 0)
                if not isinstance(qty, (int, float)):
                    _reject(
                        result,
                        f"available_ingredients[{i}].quantity",
                        "Quantity must be numeric",
                    )
                elif qty < 0:
                    _reject(
                        result,
                        f"available_ingredients[{i}].quantity",
                        "Quantity cannot be negative",
                    )

    planning_mode = data.get("planning_mode", "daily")
    if planning_mode not in _VALID_PLANNING_MODES:
        _reject(result, "planning_mode", f"Unsupported: {planning_mode}")

    return result


def _validate_profile_field(
    profile: dict,
    field_name: str,
    expected_type: type | tuple[type, ...],
    min_val: float,
    max_val: float,
    result: SecurityCheckpointResult,
    optional: bool = False,
) -> None:
    if field_name not in profile or profile[field_name] is None:
        if not optional:
            _reject(result, field_name, f"Missing required field: {field_name}")
        return
    val = profile[field_name]
    if not isinstance(val, expected_type):
        _reject(
            result,
            field_name,
            f"Expected {expected_type}, got {type(val).__name__}: {val}",
        )
        return
    if val < min_val or val > max_val:
        _reject(
            result,
            field_name,
            f"Out of range [{min_val}, {max_val}]: {val}",
        )


def _reject(result: SecurityCheckpointResult, field: str | None, detail: str) -> None:
    result.validation_errors.append(detail)
    result.events.append(
        SecurityEvent(
            category="invalid_input",
            severity="block",
            field=field,
            detail=detail,
        )
    )
    result.passed = False
    result.blocked = True


# ===================================================================
# 2. Sensitive data protection
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Scans and redacts Personally Identifiable Information (PII) from session state to protect
#   privacy and prevent sensitive leakages to the LLM.
#
# HOW IT WORKS:
# - Step 1: Creates a deep copy of the data using `_deep_copy` to avoid modifying the original data.
# - Step 2: Uses `_walk_dict` to recursively traverse keys, indices, and values in the dictionary/list.
# - Step 3: For string values, it calls `_redact_pii` to detect PII.
# - Step 4: `_redact_pii` checks the string against regex patterns (`_PII_PATTERNS`) representing emails,
#   credit cards, API keys, access tokens, phone numbers, and government IDs.
# - Step 5: Matching values are replaced with placeholders like [EMAIL REDACTED], [API KEY REDACTED], etc.
# - Step 6: Updates the redacted values into the copied dictionary using `_set_nested` and logs a SecurityEvent.
# ===================================================================
def sanitize_sensitive_data(data: dict[str, Any]) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()
    sanitized = _deep_copy(data)
    any_redacted = False

    for field_path, _value in _walk_dict(data):
        if not isinstance(_value, str):
            continue

        redacted, events = _redact_pii(_value)
        if redacted != _value:
            any_redacted = True
            _set_nested(sanitized, field_path, redacted)
            for ev in events:
                result.events.append(ev)

    if any_redacted:
        result.sanitized_data = sanitized
        _log("info", f"Sanitized {len(result.events)} PII field(s)")

    return result


def _redact_pii(text: str) -> tuple[str, list[SecurityEvent]]:
    events: list[SecurityEvent] = []
    for label, severity, pattern in _PII_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            text = pattern.sub(_redact_map[label], text)
            for m in matches[:3]:
                events.append(
                    SecurityEvent(
                        category="pii_redacted",
                        severity=severity,
                        field=None,
                        detail=f"Redacted {label}: '{_truncate(str(m), 30)}'",
                        sanitized=True,
                    )
                )
    return text, events


_redact_map: dict[str, str] = {
    "email": "[EMAIL REDACTED]",
    "phone": "[PHONE REDACTED]",
    "api_key": "[API KEY REDACTED]",
    "access_token": "[TOKEN REDACTED]",
    "credit_card": "[CREDIT CARD REDACTED]",
    "government_id": "[GOVERNMENT ID REDACTED]",
}


def _deep_copy(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _deep_copy(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_deep_copy(v) for v in data]
    return data


def _walk_dict(
    data: Any, path: tuple[str | int, ...] = ()
) -> list[tuple[tuple[str | int, ...], Any]]:
    results: list[tuple[tuple[str | int, ...], Any]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            child = (*path, k)
            results.append((child, v))
            results.extend(_walk_dict(v, child))
    elif isinstance(data, list):
        for i, v in enumerate(data):
            child = (*path, i)
            results.append((child, v))
            results.extend(_walk_dict(v, child))
    return results


def _set_nested(data: Any, path: tuple[str | int, ...], value: Any) -> None:
    for key in path[:-1]:
        data = data[key]
    data[path[-1]] = value


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[:max_len] + "..."


# ===================================================================
# 3. Prompt-injection detection
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Identifies and blocks prompt-injection attacks that attempt to bypass system rules or extract system prompts.
#
# HOW IT WORKS:
# - Step 1: Takes user message text (`_last_user_message`).
# - Step 2: Skips validation if the text is empty or not a string.
# - Step 3: Compares the text against regex patterns (`_INJECTION_PATTERNS`):
#   + ignore_system: instructions override commands.
#   + ignore_allergies: allergy constraint bypass commands (medical risk).
#   + reveal_prompt: system prompt leakage commands.
#   + reveal_secrets: credential/token leakage commands.
#   + bypass_validation: security check bypass commands.
#   + new_identity: persona hijack commands.
#   + forget_previous: context erase commands.
# - Step 4: If any pattern matches, it marks `passed = False` and `blocked = True`, and logs a high-severity SecurityEvent.
# ===================================================================
def detect_prompt_injection(
    text: str, source_label: str = "user_input"
) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()

    if not isinstance(text, str) or not text.strip():
        return result

    for injection_id, pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            result.passed = False
            result.blocked = True
            result.events.append(
                SecurityEvent(
                    category="prompt_injection",
                    severity="high",
                    field=source_label,
                    detail=(
                        f"Detected injection pattern '{injection_id}': "
                        f"'{_truncate(match.group(), 60)}'"
                    ),
                )
            )
            _log("warning", f"Prompt injection blocked ({injection_id})")

    return result


# ===================================================================
# 4. Business-rule validation
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Validates that the user profile details satisfy crucial business rules (e.g. calorie range, budget range, allergies format, and dietary preferences).
#
# HOW IT WORKS:
# - Step 1: Checks if `profile` is a dictionary, rejecting and returning errors if it's not.
# - Step 2: Validates `daily_calorie_target` against [_CALORIE_MIN (500), _CALORIE_MAX (10,000)].
# - Step 3: Validates `budget` against [0, _BUDGET_MAX (10,000)].
# - Step 4: Validates the list of allergies (`allergies`), ensuring it's a list and items are non-empty strings.
# - Step 5: Checks user's dietary preferences (`dietary_preferences`) against permitted values (`_VALID_DIETARY_PREFERENCES`).
# ===================================================================
def validate_business_rules(
    profile: dict[str, Any],
    meal_plan: list[dict[str, Any]] | None = None,
) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()

    if not isinstance(profile, dict):
        _reject(result, "user_profile", "Profile must be a dict")
        return result

    _validate_profile_field(
        profile,
        "daily_calorie_target",
        (int, float),
        _CALORIE_MIN,
        _CALORIE_MAX,
        result,
    )

    _validate_profile_field(
        profile, "budget", (int, float), 0, _BUDGET_MAX, result, optional=True
    )

    if "allergies" in profile:
        allergies = profile["allergies"]
        if not isinstance(allergies, list):
            _reject(result, "allergies", "Allergies must be a list")
        for allergy in allergies:
            if not isinstance(allergy, str) or not allergy.strip():
                _reject(
                    result,
                    "allergies",
                    f"Invalid allergy entry: {allergy}",
                )

    if "dietary_preferences" in profile:
        prefs = profile["dietary_preferences"]
        if isinstance(prefs, list):
            for p in prefs:
                if p.lower() not in _VALID_DIETARY_PREFERENCES:
                    result.validation_errors.append(
                        f"Unsupported dietary preference: {p}"
                    )
                    result.events.append(
                        SecurityEvent(
                            category="invalid_input",
                            severity="warning",
                            field="dietary_preferences",
                            detail=f"Unsupported preference: {p}",
                        )
                    )

    return result


# ===================================================================
# 5. Inventory validation
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Validates and normalizes the user's available ingredient list.
# - Rejects unknown ingredients and merges duplicate ingredients with identical units.
#
# HOW IT WORKS:
# - Step 1: Confirms the `inventory` parameter is a list.
# - Step 2: Iterates over the items, extracting raw name, quantity, and unit.
# - Step 3: Standardizes ingredient names via `normalize_ingredient_name`.
# - Step 4: Resolves units via `_resolve_unit` using UNIT_ALIASES map.
# - Step 5: Checks if the resolved ingredient is recognized in our database (`_KNOWN_INGREDIENTS`).
#   If not, it calls `_reject` to ensure safety constraints.
# - Step 6: Accumulates quantities of matching name/unit ingredient tuples.
# - Step 7: De-duplicates and merges ingredients using `_deduplicate_inventory`.
# ===================================================================
def validate_inventory(inventory: list[dict[str, Any]]) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()

    if not isinstance(inventory, list):
        _reject(result, "available_ingredients", "Inventory must be a list")
        return result

    seen: dict[tuple[str, str], float] = {}
    for i, ing in enumerate(inventory):
        raw_name = ing.get("name", "")
        raw_qty = ing.get("quantity", 0)
        raw_unit = ing.get("unit", "")

        if not isinstance(raw_name, str) or not raw_name.strip():
            _reject(
                result,
                f"available_ingredients[{i}]",
                f"Missing or empty name: {ing}",
            )
            continue

        name = normalize_ingredient_name(raw_name)
        unit = _resolve_unit(raw_unit)
        qty = float(raw_qty) if isinstance(raw_qty, (int, float)) else 0.0

        if name not in _KNOWN_INGREDIENTS:
            _reject(
                result,
                f"available_ingredients[{i}].name",
                f"Unrecognized ingredient: '{raw_name}' (resolved: '{name}')",
            )
            continue

        key = (name, unit)
        seen[key] = seen.get(key, 0) + qty
        ing["name"] = name
        ing["unit"] = unit
        ing["quantity"] = seen[key]

    if result.blocked:
        return result

    deduplicated = _deduplicate_inventory(inventory)
    _log(
        "info",
        f"Inventory validated: {len(deduplicated)} unique ingredients",
    )

    return result


def _resolve_unit(raw: str) -> str:
    cleaned = raw.strip().lower().rstrip(".").strip()
    return UNIT_ALIASES.get(cleaned, cleaned)


def _deduplicate_inventory(inventory: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for ing in inventory:
        name = ing.get("name", "")
        qty = ing.get("quantity", 0)
        unit = ing.get("unit", "")
        key = f"{name}:{unit}"
        if key in merged:
            merged[key]["quantity"] += qty
        else:
            merged[key] = {**ing, "quantity": qty}
    return list(merged.values())


# ===================================================================
# 6. Output validation
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Validates LLM-generated meal plans against nutritional requirements, allergy constraints, and budgets.
#
# HOW IT WORKS:
# - Step 1: Extracts daily calorie target, user allergies, and budget from the user profile.
# - Step 2: Loops through each day in the meal plan.
# - Step 3: Verifies daily total calories match the target within +/- 10% (`_MACRO_TOLERANCE`).
# - Step 4: Ensures no duplicate meals are scheduled across multiple days.
# - Step 5: Checks individual ingredients in the generated meals against the user's allergy list.
#   Triggers an error if a matching allergen is found.
# - Step 6: Sums the total plan cost via `cal_cost` and verifies it doesn't exceed the user's budget.
# - Sets `passed = False` if any violation is found, but does not block (permits retry/regeneration).
# ===================================================================
def validate_output(
    meal_plan: list[dict[str, Any]],
    profile: dict[str, Any],
) -> SecurityCheckpointResult:
    result = SecurityCheckpointResult()

    if not isinstance(meal_plan, list):
        result.validation_errors.append("meal_plan must be a list")
        result.passed = False
        return result

    calorie_target = profile.get("daily_calorie_target", 0)
    allergies = profile.get("allergies", [])
    budget = profile.get("budget", None)

    seen_recipes: set[str] = set()
    day_count = len(meal_plan)

    for day in meal_plan:
        day_name = day.get("day", "unknown")
        nutrition = day.get("total_nutrition", {})
        meals = day.get("meals", [])

        day_cal = nutrition.get("calories", 0)

        if calorie_target > 0:
            cal_lower = calorie_target * (1 - _MACRO_TOLERANCE)
            cal_upper = calorie_target * (1 + _MACRO_TOLERANCE)
            if not (cal_lower <= day_cal <= cal_upper):
                result.validation_errors.append(
                    f"{day_name}: calories {day_cal} outside "
                    f"[{cal_lower:.0f}, {cal_upper:.0f}] (target {calorie_target})"
                )
                result.passed = False

        for meal in meals:
            meal_name = ""
            if isinstance(meal, str):
                meal_name = meal
            elif isinstance(meal, dict):
                meal_name = meal.get("name", "")

            if meal_name in seen_recipes and day_count > 1:
                result.validation_errors.append(
                    f"{day_name}: duplicate recipe '{meal_name}'"
                )
                result.passed = False
            seen_recipes.add(meal_name)

            if isinstance(meal, dict):
                meal_ings = meal.get("ingredients", [])
                for ing in meal_ings:
                    ing_name = ing.get("name", "") if isinstance(ing, dict) else ""
                    if ing_name in allergies:
                        result.validation_errors.append(
                            f"{day_name}: contains allergen '{ing_name}' "
                            f"in meal '{meal_name}'"
                        )
                        result.passed = False

    if budget is not None and budget > 0:
        plan_cost = sum(cal_cost(day) for day in meal_plan)
        if plan_cost > budget:
            result.validation_errors.append(
                f"Total cost ${plan_cost:.2f} exceeds budget ${budget:.2f}"
            )
            result.passed = False

    return result


def cal_cost(day: dict) -> float:
    total = 0.0
    meals = day.get("meals", [])
    for meal in meals:
        if isinstance(meal, dict):
            qty = meal.get("estimated_cost", 0) or meal.get("cost", 0)
            total += qty if isinstance(qty, (int, float)) else 0
    return total


# ===================================================================
# 7. Main orchestrator
# -------------------------------------------------------------------
# WHAT IT DOES:
# - Orchestrates the entire checkpoint validation flow dynamically depending on the current step.
#
# HOW IT WORKS:
# - Step 1: Initializes a combined `SecurityCheckpointResult` (passed=True by default).
# - Step 2: Based on the `step` argument:
#   + step "input", "profile", or "onboarding" -> runs `validate_input`.
#   + step "input", "profile", "onboarding", "recipe", or "meal_plan" -> runs `detect_prompt_injection`.
#   + step "profile", "recipe", "meal_plan", or "shopping" -> runs `sanitize_sensitive_data`.
#   + step "profile", "recipe", or "meal_plan" -> runs `validate_business_rules`.
#   + step "inventory" or "input" -> runs `validate_inventory`.
#   + step "output" or general output validation -> runs `validate_output`.
# - Step 3: Merges all errors, events, and block states into the unified `combined` result via `_merge`.
# - Step 4: Returns the result. If `combined.blocked == True`, workflow stops execution.
# ===================================================================
def run_security_checkpoint(
    session_state: dict[str, Any],
    step: str = "",
) -> SecurityCheckpointResult:
    combined = SecurityCheckpointResult(passed=True)

    if step in ("", "input", "profile", "onboarding"):
        r = validate_input(session_state)
        _merge(combined, r)

    if step in ("", "input", "profile", "onboarding", "recipe", "meal_plan"):
        r = detect_prompt_injection(
            str(session_state.get("_last_user_message", "")),
            source_label="_last_user_message",
        )
        _merge(combined, r)

    if step in ("", "profile", "recipe", "meal_plan", "shopping"):
        profile = session_state.get("user_profile", {})
        r = sanitize_sensitive_data({"user_profile": profile})
        if r.sanitized_data:
            combined.sanitized_data = r.sanitized_data
        for ev in r.events:
            combined.events.append(ev)

    if step in ("", "profile", "recipe", "meal_plan"):
        profile = session_state.get("user_profile", {})
        meal_plan = session_state.get("meal_plan")
        r = validate_business_rules(profile, meal_plan)
        _merge(combined, r)

    if step in ("", "inventory", "input"):
        inventory = session_state.get("available_ingredients", [])
        r = validate_inventory(inventory)
        _merge(combined, r)

    if step == "output" or (step == "" and "meal_plan" in session_state):
        profile = session_state.get("user_profile", {})
        meal_plan = session_state.get("meal_plan", [])
        if meal_plan:
            r = validate_output(meal_plan, profile)
            _merge(combined, r)

    if combined.blocked:
        _log("warning", f"Checkpoint BLOCKED at step='{step}'")

    return combined


def _merge(target: SecurityCheckpointResult, source: SecurityCheckpointResult) -> None:
    if not source.passed:
        target.passed = False
    if source.blocked:
        target.blocked = True
    target.events.extend(source.events)
    target.validation_errors.extend(source.validation_errors)
    if source.sanitized_data and not target.sanitized_data:
        target.sanitized_data = source.sanitized_data
