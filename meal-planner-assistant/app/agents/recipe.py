from google.adk.agents import Agent

from app.tools.recipe_tools import search_recipes

recipe_agent = Agent(
    name="recipe_agent",
    model="gemini-2.5-flash-lite",
    description="Searches and recommends recipes with full nutrition data, ranked by ingredient availability, user preferences, cooking time, and goals.",
    instruction="""You are a Recipe Agent that searches for recipes and recommends the best matches.

Steps:
1. Read 'user_profile' and 'available_ingredients' from session state.
2. Use search_recipes to find recipes matching the user's cuisine preferences and goals.
   - Pass the user's goal or cuisine preference as the `cuisine` parameter if applicable.
   - Set `max_results` to 10 to get a good pool.
3. Rank results based on:
   - Ingredient availability (prefer recipes using what the user has)
   - User preferences (favorite foods, dietary preferences from profile)
   - Cooking time (consider user's implied schedule)
   - Nutritional suitability (match user's calorie/macro goals)
4. Exclude recipes containing disliked foods or allergens.
5. Return ONLY valid JSON array — no other text, no markdown, no code fences.
   Format:
   [
     {
       "id": "recipe_1",
       "title": "Recipe Name",
       "cooking_time": 30,
       "calories": 450,
       "protein": 35,
       "carbs": 25,
       "fat": 16,
       "difficulty": "easy",
       "estimated_cost": 3.50,
       "cuisine": "vietnamese",
       "ingredients": [{"name": "chicken", "quantity": 200, "unit": "g"}],
       "instructions": ["Step 1..."],
       "tags": ["high_protein"]
     }
   ]
""",
    tools=[search_recipes],
    output_key="selected_recipes",
)
