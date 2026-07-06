from google.adk.agents.context import Context
from google.adk.events.request_input import RequestInput
from google.adk.workflow import DEFAULT_ROUTE, node

from app.tools.cost_estimator import estimate_grocery_cost
from app.tools.normalize_ingredients import normalize_ingredients
from app.tools.shopping_list import generate_optimized_shopping_list


@node
async def inventory_fn(ctx: Context) -> dict:
    """Normalize raw ingredients from session state into structured items.

    Non-AI node — calls the deterministic normalize_ingredients tool directly.
    """
    raw = ctx.state.get("available_ingredients", [])
    if not raw:
        return {"items": []}

    normalized = await normalize_ingredients(raw)
    ctx.state["available_ingredients"] = normalized
    return {"items": normalized}


@node
async def shopping_fn(ctx: Context) -> dict:
    """Generate an optimized shopping list and estimate its cost.

    Non-AI node — calls deterministic tools directly without a Gemini agent.
    """
    selected_recipes = ctx.state.get("selected_recipes", [])
    available_ingredients = ctx.state.get("available_ingredients", [])

    shopping_items = await generate_optimized_shopping_list(
        selected_recipes, available_ingredients
    )
    cost_info = await estimate_grocery_cost(shopping_items)

    result = {
        "items": shopping_items,
        "total_cost": cost_info.get("total", 0),
        "budget_exceeded": False,
        "budget_gap": 0,
    }

    user_profile = ctx.state.get("user_profile", {})
    budget = user_profile.get("budget", 0)
    if budget and cost_info.get("total", 0) > budget:
        result["budget_exceeded"] = True
        result["budget_gap"] = cost_info["total"] - budget

    ctx.state["shopping_list"] = result
    return result


@node
async def budget_feedback_fn(ctx: Context):
    """Check if the shopping list exceeds the user's budget.

    Human-in-the-loop: if over budget, asks user to choose swap/reduce/proceed.
    """
    shopping = ctx.state.get("shopping_list", {})
    if not shopping.get("budget_exceeded", False):
        ctx.route = DEFAULT_ROUTE
        yield {"action": "proceed", "budget_ok": True}
        return

    if ctx.resume_inputs:
        user_text = str(ctx.resume_inputs.get("budget_feedback", ""))
        clean = user_text.strip().lower()[:20]

        if "swap" in clean or clean == "a":
            ctx.state.pop("selected_recipes", None)
            ctx.state.pop("shopping_list", None)
            ctx.route = "swap_recipes"
            yield {"action": "swap_recipes"}
            return

        if "reduce" in clean or "portion" in clean or clean == "b":
            ctx.state.pop("meal_plan", None)
            ctx.state.pop("shopping_list", None)
            ctx.route = "reduce_portions"
            yield {"action": "reduce_portions"}
            return

        ctx.route = DEFAULT_ROUTE
        yield {"action": "proceed"}
        return

    profile = ctx.state.get("user_profile", {})
    budget = profile.get("budget", 0)
    total = shopping.get("total_cost", 0)
    gap = shopping.get("budget_gap", total - budget)

    yield RequestInput(
        message=(
            f"Your total ${total:.2f} exceeds your ${budget:.2f} budget "
            f"(gap: ${gap:.2f}).\n\n"
            "Options:\n"
            "A — Swap to cheaper recipes\n"
            "B — Reduce portions\n"
            "C — Proceed anyway\n\n"
            "What would you like to do?"
        ),
        interrupt_id="budget_feedback",
    )


@node
async def done_fn(ctx: Context) -> dict:
    """Aggregate final results from session state."""
    return {
        "profile": ctx.state.get("user_profile"),
        "selected_recipes": ctx.state.get("selected_recipes"),
        "meal_plan": ctx.state.get("meal_plan"),
        "shopping_list": ctx.state.get("shopping_list"),
    }
