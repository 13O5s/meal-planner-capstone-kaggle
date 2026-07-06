from google.adk.apps import App
from google.adk.workflow import DEFAULT_ROUTE, START, Workflow

from app.agents.meal_plan import meal_plan_agent
from app.agents.profile import profile_agent
from app.agents.recipe import recipe_agent
from app.workflow_nodes import (
    budget_feedback_fn,
    done_fn,
    inventory_fn,
    shopping_fn,
)

# =============================================================================
# AGENT WORKFLOW: meal_planner_workflow
# =============================================================================
# Graph-based workflow that orchestrates the meal planning pipeline through
# 7 visible nodes:
#
#   3 AI-powered Agents (Gemini):
#     - profile_agent:   Collects user health/fitness profile via conversation
#     - recipe_agent:    Searches & ranks recipes matching user preferences
#     - meal_plan_agent: Generates weekly plan, validates nutrition
#
#   4 non-AI function nodes:
#     - inventory_fn:   Normalizes raw ingredient input (deterministic)
#     - shopping_fn:    Optimizes shopping list + estimates cost
#     - budget_feedback_fn:  Human-in-the-loop for budget overage
#     - done_fn:        Aggregates and returns final results
#
# Conditional routing:
#   budget_feedback_fn → "swap_recipes" → back to recipe_agent
#                      → "reduce_portions" → back to meal_plan_agent
#                      → default → done_fn
# =============================================================================

root_agent = Workflow(
    name="meal_planner_workflow",
    description="Meal planning pipeline: profile → inventory → recipe → "
    "meal plan → shopping → budget check → done",
    edges=[
        (START, profile_agent),
        (profile_agent, inventory_fn),
        (inventory_fn, recipe_agent),
        (recipe_agent, meal_plan_agent),
        (meal_plan_agent, shopping_fn),
        (shopping_fn, budget_feedback_fn),
        (
            budget_feedback_fn,
            {
                "swap_recipes": recipe_agent,
                "reduce_portions": meal_plan_agent,
                DEFAULT_ROUTE: done_fn,
            },
        ),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
