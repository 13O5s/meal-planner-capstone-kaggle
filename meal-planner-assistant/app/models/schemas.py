from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    age: int | None = None
    gender: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    target_weight_kg: float | None = None
    activity_level: str | None = None
    daily_calorie_target: int | None = None
    favorite_foods: list[str] = []
    disliked_foods: list[str] = []
    allergies: list[str] = []
    dietary_preferences: list[str] = []
    budget: float | None = None
    meals_per_day: int = 3
    goal: str = "healthy"


class IngredientItem(BaseModel):
    name: str
    quantity: float
    unit: str
    available: bool = False


class NormalizedIngredient(BaseModel):
    name: str
    quantity: float
    unit: str
    original_text: str


class Recipe(BaseModel):
    id: str
    name: str
    ingredients: list[IngredientItem]
    instructions: str
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    cuisine: str
    nutrition: Optional["NutritionInfo"] = None


class NutritionInfo(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float


class ShoppingListItem(BaseModel):
    ingredient_name: str
    total_quantity: float
    unit: str
    estimated_cost: float
    category: str


class MealPlan(BaseModel):
    day: str
    meals: list[str]
    total_nutrition: NutritionInfo


class MealPlanResult(BaseModel):
    plan: list[MealPlan]
    goal: str
    total_cost_estimate: float
    validation: Optional["NutritionValidation"] = None


class NutritionValidation(BaseModel):
    meets_calories: bool
    meets_protein: bool
    meets_carbs: bool
    meets_fat: bool
    details: str
