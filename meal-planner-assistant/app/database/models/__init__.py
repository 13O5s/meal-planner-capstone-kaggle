from app.database.models.base import Base
from app.database.models.history import FavoriteRecipe, MealHistory
from app.database.models.ingredient import (
    Ingredient,
    IngredientAlias,
    IngredientNutrition,
)
from app.database.models.inventory import InventoryItem
from app.database.models.notification import Notification
from app.database.models.recipe import (
    Recipe,
    RecipeIngredient,
    RecipeNutrition,
    RecipeTag,
    Tag,
)
from app.database.models.saved_plan import SavedPlan
from app.database.models.saved_shopping import SavedShoppingItem, SavedShoppingList
from app.database.models.user import (
    DietaryRestriction,
    FoodPreference,
    User,
    UserAllergy,
    UserProfile,
)

__all__ = [
    "Base",
    "DietaryRestriction",
    "FavoriteRecipe",
    "FoodPreference",
    "Ingredient",
    "IngredientAlias",
    "IngredientNutrition",
    "InventoryItem",
    "MealHistory",
    "Notification",
    "Recipe",
    "RecipeIngredient",
    "RecipeNutrition",
    "RecipeTag",
    "SavedPlan",
    "SavedShoppingItem",
    "SavedShoppingList",
    "Tag",
    "User",
    "UserAllergy",
    "UserProfile",
]
