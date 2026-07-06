import random

STATIC_MEALS = {
    "Breakfast": [
        {"type": "Breakfast", "name": "Oatmeal with Banana & Honey", "calories": 320, "protein": 12, "carbs": 52, "fat": 6, "time": "15 min", "cost": 1.50},
        {"type": "Breakfast", "name": "Scrambled Eggs with Toast", "calories": 380, "protein": 22, "carbs": 28, "fat": 18, "time": "10 min", "cost": 1.20},
        {"type": "Breakfast", "name": "Greek Yogurt & Granola", "calories": 280, "protein": 18, "carbs": 38, "fat": 5, "time": "5 min", "cost": 1.80},
        {"type": "Breakfast", "name": "Avocado Toast & Eggs", "calories": 350, "protein": 16, "carbs": 30, "fat": 20, "time": "12 min", "cost": 2.50},
        {"type": "Breakfast", "name": "Protein Pancakes", "calories": 340, "protein": 25, "carbs": 40, "fat": 10, "time": "15 min", "cost": 2.00},
        {"type": "Breakfast", "name": "Smoothie Bowl", "calories": 350, "protein": 15, "carbs": 55, "fat": 8, "time": "10 min", "cost": 2.00},
        {"type": "Breakfast", "name": "French Toast", "calories": 350, "protein": 14, "carbs": 42, "fat": 16, "time": "15 min", "cost": 1.50},
    ],
    "Lunch": [
        {"type": "Lunch", "name": "Grilled Chicken Salad", "calories": 400, "protein": 35, "carbs": 18, "fat": 22, "time": "15 min", "cost": 4.00},
        {"type": "Lunch", "name": "Turkey Sandwich", "calories": 380, "protein": 30, "carbs": 35, "fat": 12, "time": "10 min", "cost": 3.00},
        {"type": "Lunch", "name": "Quinoa Buddha Bowl", "calories": 420, "protein": 18, "carbs": 48, "fat": 16, "time": "20 min", "cost": 3.50},
        {"type": "Lunch", "name": "Tuna Salad Wrap", "calories": 360, "protein": 28, "carbs": 30, "fat": 14, "time": "10 min", "cost": 3.00},
        {"type": "Lunch", "name": "Minestrone Soup", "calories": 300, "protein": 12, "carbs": 35, "fat": 8, "time": "25 min", "cost": 2.50},
        {"type": "Lunch", "name": "Chicken & Vegetable Stir Fry", "calories": 450, "protein": 38, "carbs": 25, "fat": 16, "time": "25 min", "cost": 3.50},
        {"type": "Lunch", "name": "Caprese Salad", "calories": 320, "protein": 16, "carbs": 10, "fat": 24, "time": "10 min", "cost": 3.00},
    ],
    "Dinner": [
        {"type": "Dinner", "name": "Grilled Steak with Sweet Potato", "calories": 600, "protein": 45, "carbs": 42, "fat": 26, "time": "30 min", "cost": 6.00},
        {"type": "Dinner", "name": "Baked Salmon with Vegetables", "calories": 520, "protein": 40, "carbs": 20, "fat": 28, "time": "30 min", "cost": 5.00},
        {"type": "Dinner", "name": "Chicken Curry with Rice", "calories": 520, "protein": 35, "carbs": 48, "fat": 18, "time": "35 min", "cost": 4.00},
        {"type": "Dinner", "name": "Vegetable Stir Fry with Tofu", "calories": 450, "protein": 20, "carbs": 40, "fat": 18, "time": "20 min", "cost": 3.50},
        {"type": "Dinner", "name": "Beef Stir Fry", "calories": 550, "protein": 42, "carbs": 30, "fat": 24, "time": "25 min", "cost": 4.50},
        {"type": "Dinner", "name": "Lentil Pasta with Marinara", "calories": 580, "protein": 25, "carbs": 70, "fat": 12, "time": "30 min", "cost": 2.80},
        {"type": "Dinner", "name": "Roast Chicken with Vegetables", "calories": 580, "protein": 48, "carbs": 35, "fat": 22, "time": "60 min", "cost": 5.50},
    ],
}


STATIC_RECIPES: dict[str, dict] = {
    "default": {
        "ingredients": [
            {"name": "fresh mixed vegetables", "quantity": 300, "unit": "g"},
            {"name": "protein of choice", "quantity": 200, "unit": "g"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "salt", "quantity": 1, "unit": "tsp"},
            {"name": "black pepper", "quantity": 0.5, "unit": "tsp"},
        ],
        "instructions": [
            "Prepare and chop all ingredients",
            "Heat oil in a pan over medium heat",
            "Cook the protein until golden brown on all sides",
            "Add vegetables and seasonings, cook until tender",
            "Plate and serve hot",
        ],
        "nutrition": {"calories": 450, "protein": 28, "carbs": 35, "fat": 16},
    },
    "Oatmeal with Banana & Honey|Breakfast": {
        "ingredients": [
            {"name": "rolled oats", "quantity": 80, "unit": "g"},
            {"name": "banana", "quantity": 1, "unit": "piece"},
            {"name": "honey", "quantity": 1, "unit": "tbsp"},
            {"name": "milk", "quantity": 200, "unit": "ml"},
            {"name": "cinnamon", "quantity": 0.5, "unit": "tsp"},
        ],
        "instructions": [
            "Bring milk to a boil in a small saucepan",
            "Add rolled oats and reduce heat to low",
            "Cook for 5 minutes, stirring occasionally",
            "Slice banana and place on top",
            "Drizzle with honey and sprinkle cinnamon",
            "Serve warm",
        ],
        "nutrition": {"calories": 320, "protein": 12, "carbs": 52, "fat": 6},
    },
    "Grilled Chicken Salad|Lunch": {
        "ingredients": [
            {"name": "chicken breast", "quantity": 200, "unit": "g"},
            {"name": "mixed salad greens", "quantity": 150, "unit": "g"},
            {"name": "cherry tomatoes", "quantity": 100, "unit": "g"},
            {"name": "cucumber", "quantity": 0.5, "unit": "piece"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "lemon juice", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Season chicken breast with salt and pepper",
            "Grill chicken for 6-7 minutes per side until cooked through",
            "Let chicken rest for 5 minutes, then slice",
            "Toss salad greens, cherry tomatoes, and cucumber in a bowl",
            "Top with sliced chicken",
            "Drizzle with olive oil and lemon juice",
        ],
        "nutrition": {"calories": 400, "protein": 35, "carbs": 18, "fat": 22},
    },
    "Baked Salmon with Vegetables|Dinner": {
        "ingredients": [
            {"name": "salmon fillet", "quantity": 200, "unit": "g"},
            {"name": "broccoli", "quantity": 150, "unit": "g"},
            {"name": "carrots", "quantity": 100, "unit": "g"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "lemon", "quantity": 0.5, "unit": "piece"},
            {"name": "garlic powder", "quantity": 0.5, "unit": "tsp"},
            {"name": "dill", "quantity": 0.5, "unit": "tsp"},
        ],
        "instructions": [
            "Preheat oven to 200°C (400°F)",
            "Place salmon on a baking sheet lined with parchment paper",
            "Arrange broccoli and carrot slices around the salmon",
            "Drizzle everything with olive oil and season with garlic, dill, salt, and pepper",
            "Squeeze lemon juice over the salmon",
            "Bake for 15-18 minutes until salmon flakes easily",
            "Serve immediately",
        ],
        "nutrition": {"calories": 520, "protein": 40, "carbs": 20, "fat": 28},
    },
    "Chicken Curry with Rice|Dinner": {
        "ingredients": [
            {"name": "chicken thigh", "quantity": 250, "unit": "g"},
            {"name": "rice", "quantity": 150, "unit": "g"},
            {"name": "coconut milk", "quantity": 200, "unit": "ml"},
            {"name": "curry powder", "quantity": 2, "unit": "tbsp"},
            {"name": "onion", "quantity": 1, "unit": "piece"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "ginger", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Cook rice according to package directions",
            "Dice onion, mince garlic and ginger",
            "Heat oil in a large pan and sauté onion until soft",
            "Add garlic, ginger, and curry powder, cook for 1 minute",
            "Add chicken pieces and brown on all sides",
            "Pour in coconut milk, bring to a simmer",
            "Cook for 15 minutes until chicken is tender and sauce thickens",
            "Serve over rice",
        ],
        "nutrition": {"calories": 520, "protein": 35, "carbs": 48, "fat": 18},
    },
    "Grilled Steak with Sweet Potato|Dinner": {
        "ingredients": [
            {"name": "beef steak", "quantity": 250, "unit": "g"},
            {"name": "sweet potato", "quantity": 200, "unit": "g"},
            {"name": "butter", "quantity": 1, "unit": "tbsp"},
            {"name": "rosemary", "quantity": 1, "unit": "sprig"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Preheat grill or cast-iron pan to high heat",
            "Season steak generously with salt and pepper",
            "Pierce sweet potato with fork and microwave for 5 minutes",
            "Grill steak 4-5 minutes per side for medium-rare",
            "Let steak rest for 5 minutes",
            "Slice sweet potato and serve with butter and rosemary",
        ],
        "nutrition": {"calories": 600, "protein": 45, "carbs": 42, "fat": 26},
    },
    "Greek Yogurt & Granola|Breakfast": {
        "ingredients": [
            {"name": "greek yogurt", "quantity": 200, "unit": "g"},
            {"name": "granola", "quantity": 50, "unit": "g"},
            {"name": "honey", "quantity": 1, "unit": "tbsp"},
            {"name": "mixed berries", "quantity": 80, "unit": "g"},
        ],
        "instructions": [
            "Spoon Greek yogurt into a bowl",
            "Top with granola and mixed berries",
            "Drizzle with honey",
            "Serve immediately",
        ],
        "nutrition": {"calories": 280, "protein": 18, "carbs": 38, "fat": 5},
    },
    "Turkey Sandwich|Lunch": {
        "ingredients": [
            {"name": "whole wheat bread", "quantity": 2, "unit": "slices"},
            {"name": "turkey breast", "quantity": 100, "unit": "g"},
            {"name": "lettuce", "quantity": 30, "unit": "g"},
            {"name": "tomato", "quantity": 3, "unit": "slices"},
            {"name": "mayonnaise", "quantity": 1, "unit": "tbsp"},
            {"name": "mustard", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Toast bread slices until golden",
            "Spread mayonnaise on one slice, mustard on the other",
            "Layer turkey breast, lettuce, and tomato slices",
            "Close sandwich and cut diagonally",
            "Serve with a side of chips or salad",
        ],
        "nutrition": {"calories": 380, "protein": 30, "carbs": 35, "fat": 12},
    },
    "Scrambled Eggs with Toast|Breakfast": {
        "ingredients": [
            {"name": "eggs", "quantity": 3, "unit": "piece"},
            {"name": "whole wheat bread", "quantity": 2, "unit": "slices"},
            {"name": "milk", "quantity": 30, "unit": "ml"},
            {"name": "butter", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Crack eggs into a bowl, add milk, and whisk until frothy",
            "Heat butter in a non-stick pan over medium heat",
            "Pour in eggs and stir gently until just set",
            "Toast bread slices until golden",
            "Serve eggs alongside toast",
        ],
        "nutrition": {"calories": 380, "protein": 22, "carbs": 28, "fat": 18},
    },
    "Avocado Toast & Eggs|Breakfast": {
        "ingredients": [
            {"name": "whole wheat bread", "quantity": 2, "unit": "slices"},
            {"name": "avocado", "quantity": 1, "unit": "piece"},
            {"name": "eggs", "quantity": 2, "unit": "piece"},
            {"name": "lemon juice", "quantity": 1, "unit": "tsp"},
            {"name": "salt", "quantity": 0.5, "unit": "tsp"},
            {"name": "black pepper", "quantity": 0.25, "unit": "tsp"},
        ],
        "instructions": [
            "Toast bread slices until golden",
            "Mash avocado with lemon juice, salt, and pepper",
            "Fry eggs sunny-side up or poach to preference",
            "Spread avocado mash on toast",
            "Top with eggs and serve immediately",
        ],
        "nutrition": {"calories": 350, "protein": 16, "carbs": 30, "fat": 20},
    },
    "Protein Pancakes|Breakfast": {
        "ingredients": [
            {"name": "oats", "quantity": 80, "unit": "g"},
            {"name": "eggs", "quantity": 2, "unit": "piece"},
            {"name": "banana", "quantity": 1, "unit": "piece"},
            {"name": "milk", "quantity": 60, "unit": "ml"},
            {"name": "honey", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Blend oats into a fine flour",
            "Add eggs, banana, and milk, blend until smooth",
            "Heat a non-stick pan over medium heat",
            "Pour batter and cook until bubbles form, then flip",
            "Drizzle with honey and serve",
        ],
        "nutrition": {"calories": 340, "protein": 25, "carbs": 40, "fat": 10},
    },
    "Smoothie Bowl|Breakfast": {
        "ingredients": [
            {"name": "banana", "quantity": 1, "unit": "piece"},
            {"name": "mixed berries", "quantity": 100, "unit": "g"},
            {"name": "greek yogurt", "quantity": 100, "unit": "g"},
            {"name": "honey", "quantity": 1, "unit": "tbsp"},
            {"name": "granola", "quantity": 30, "unit": "g"},
        ],
        "instructions": [
            "Blend banana, mixed berries, yogurt, and honey until smooth and thick",
            "Pour into a bowl",
            "Top with granola and extra berries",
            "Serve immediately",
        ],
        "nutrition": {"calories": 350, "protein": 15, "carbs": 55, "fat": 8},
    },
    "French Toast|Breakfast": {
        "ingredients": [
            {"name": "whole wheat bread", "quantity": 3, "unit": "slices"},
            {"name": "eggs", "quantity": 2, "unit": "piece"},
            {"name": "milk", "quantity": 60, "unit": "ml"},
            {"name": "honey", "quantity": 1, "unit": "tbsp"},
            {"name": "cinnamon", "quantity": 0.5, "unit": "tsp"},
        ],
        "instructions": [
            "Whisk eggs, milk, and cinnamon together in a shallow dish",
            "Dip bread slices into the mixture, coating both sides",
            "Heat a buttered pan over medium heat",
            "Cook each slice 2-3 minutes per side until golden",
            "Drizzle with honey and serve",
        ],
        "nutrition": {"calories": 350, "protein": 14, "carbs": 42, "fat": 16},
    },
    "Quinoa Buddha Bowl|Lunch": {
        "ingredients": [
            {"name": "quinoa", "quantity": 100, "unit": "g"},
            {"name": "chicken breast", "quantity": 150, "unit": "g"},
            {"name": "avocado", "quantity": 0.5, "unit": "piece"},
            {"name": "cherry tomatoes", "quantity": 80, "unit": "g"},
            {"name": "cucumber", "quantity": 0.5, "unit": "piece"},
            {"name": "lemon juice", "quantity": 1, "unit": "tbsp"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Cook quinoa according to package directions and let cool",
            "Grill chicken breast and slice",
            "Chop avocado, cucumber, and halve cherry tomatoes",
            "Arrange all ingredients in a bowl",
            "Drizzle with olive oil and lemon juice",
        ],
        "nutrition": {"calories": 420, "protein": 18, "carbs": 48, "fat": 16},
    },
    "Tuna Salad Wrap|Lunch": {
        "ingredients": [
            {"name": "canned tuna", "quantity": 100, "unit": "g"},
            {"name": "whole wheat bread", "quantity": 1, "unit": "slices"},
            {"name": "lettuce", "quantity": 30, "unit": "g"},
            {"name": "tomato", "quantity": 0.5, "unit": "piece"},
            {"name": "onion", "quantity": 0.25, "unit": "piece"},
            {"name": "lemon juice", "quantity": 1, "unit": "tsp"},
        ],
        "instructions": [
            "Drain tuna and flake into a bowl",
            "Dice onion and tomato finely",
            "Mix tuna with onion, tomato, and lemon juice",
            "Lay lettuce on wrap, spoon tuna mixture on top",
            "Wrap tightly, cut in half, and serve",
        ],
        "nutrition": {"calories": 360, "protein": 28, "carbs": 30, "fat": 14},
    },
    "Minestrone Soup|Lunch": {
        "ingredients": [
            {"name": "mixed beans", "quantity": 100, "unit": "g"},
            {"name": "pasta", "quantity": 50, "unit": "g"},
            {"name": "tomato sauce", "quantity": 200, "unit": "ml"},
            {"name": "carrot", "quantity": 1, "unit": "piece"},
            {"name": "onion", "quantity": 0.5, "unit": "piece"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Dice onion, carrot, and mince garlic",
            "Sauté onion and garlic in olive oil until soft",
            "Add carrot, tomato sauce, and 500ml water",
            "Stir in beans and pasta, bring to a boil",
            "Simmer for 20 minutes until pasta is tender",
            "Season with salt and pepper, serve hot",
        ],
        "nutrition": {"calories": 300, "protein": 12, "carbs": 35, "fat": 8},
    },
    "Chicken & Vegetable Stir Fry|Lunch": {
        "ingredients": [
            {"name": "chicken breast", "quantity": 200, "unit": "g"},
            {"name": "mixed vegetables", "quantity": 200, "unit": "g"},
            {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
            {"name": "sesame oil", "quantity": 1, "unit": "tbsp"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Slice chicken breast into thin strips",
            "Mince garlic and chop mixed vegetables",
            "Heat olive oil in a wok over high heat",
            "Stir-fry chicken until golden, 4-5 minutes",
            "Add garlic and vegetables, cook 3 minutes",
            "Add soy sauce and sesame oil, toss well",
        ],
        "nutrition": {"calories": 450, "protein": 38, "carbs": 25, "fat": 16},
    },
    "Caprese Salad|Lunch": {
        "ingredients": [
            {"name": "mozzarella", "quantity": 150, "unit": "g"},
            {"name": "tomato", "quantity": 2, "unit": "piece"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "lettuce", "quantity": 50, "unit": "g"},
            {"name": "salt", "quantity": 0.5, "unit": "tsp"},
            {"name": "black pepper", "quantity": 0.25, "unit": "tsp"},
        ],
        "instructions": [
            "Slice mozzarella and tomatoes into even rounds",
            "Arrange on a plate alternating cheese and tomato",
            "Drizzle with olive oil",
            "Season with salt and pepper",
            "Serve with fresh lettuce on the side",
        ],
        "nutrition": {"calories": 320, "protein": 16, "carbs": 10, "fat": 24},
    },
    "Vegetable Stir Fry with Tofu|Dinner": {
        "ingredients": [
            {"name": "tofu", "quantity": 200, "unit": "g"},
            {"name": "mixed vegetables", "quantity": 250, "unit": "g"},
            {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
            {"name": "sesame oil", "quantity": 1, "unit": "tbsp"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Press tofu and cut into cubes",
            "Mince garlic and chop mixed vegetables",
            "Heat olive oil in a wok over high heat",
            "Fry tofu until golden on all sides",
            "Add garlic and vegetables, stir-fry 4 minutes",
            "Add soy sauce and sesame oil, toss and serve",
        ],
        "nutrition": {"calories": 450, "protein": 20, "carbs": 40, "fat": 18},
    },
    "Beef Stir Fry|Dinner": {
        "ingredients": [
            {"name": "ground beef", "quantity": 250, "unit": "g"},
            {"name": "mixed vegetables", "quantity": 200, "unit": "g"},
            {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
            {"name": "sesame oil", "quantity": 1, "unit": "tbsp"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Mince garlic and chop mixed vegetables",
            "Heat olive oil in a wok over high heat",
            "Brown the ground beef, breaking it apart",
            "Add garlic and stir for 30 seconds",
            "Add mixed vegetables and cook 4 minutes",
            "Pour in soy sauce and sesame oil, toss well",
        ],
        "nutrition": {"calories": 550, "protein": 42, "carbs": 30, "fat": 24},
    },
    "Lentil Pasta with Marinara|Dinner": {
        "ingredients": [
            {"name": "pasta", "quantity": 150, "unit": "g"},
            {"name": "tomato sauce", "quantity": 200, "unit": "ml"},
            {"name": "lentils", "quantity": 100, "unit": "g"},
            {"name": "onion", "quantity": 0.5, "unit": "piece"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
        ],
        "instructions": [
            "Cook pasta according to package directions",
            "Cook lentils separately until tender, drain",
            "Dice onion and mince garlic",
            "Sauté onion and garlic in olive oil until soft",
            "Add tomato sauce and cooked lentils, simmer 10 minutes",
            "Toss sauce with pasta and serve",
        ],
        "nutrition": {"calories": 580, "protein": 25, "carbs": 70, "fat": 12},
    },
    "Roast Chicken with Vegetables|Dinner": {
        "ingredients": [
            {"name": "chicken breast", "quantity": 250, "unit": "g"},
            {"name": "broccoli", "quantity": 150, "unit": "g"},
            {"name": "carrot", "quantity": 2, "unit": "piece"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "garlic", "quantity": 3, "unit": "cloves"},
            {"name": "salt", "quantity": 1, "unit": "tsp"},
            {"name": "black pepper", "quantity": 0.5, "unit": "tsp"},
        ],
        "instructions": [
            "Preheat oven to 200°C (400°F)",
            "Season chicken breast with salt, pepper, and minced garlic",
            "Chop broccoli and carrot into even pieces",
            "Arrange chicken and vegetables on a baking sheet",
            "Drizzle with olive oil and roast for 25-30 minutes",
            "Let rest 5 minutes before serving",
        ],
        "nutrition": {"calories": 580, "protein": 48, "carbs": 35, "fat": 22},
    },
}


def get_fallback_meal(meal_type: str, original_name: str = "") -> dict:
    pool = STATIC_MEALS.get(meal_type, STATIC_MEALS["Lunch"])
    filtered = [m for m in pool if m["name"] != original_name] if original_name else pool
    return random.choice(filtered) if filtered else random.choice(pool)


def get_fallback_recipe(meal_name: str, meal_type: str) -> dict:
    key = f"{meal_name}|{meal_type}"
    return STATIC_RECIPES.get(key, STATIC_RECIPES["default"])


def get_fallback_day(day_name: str) -> dict:
    return {
        "day": day_name,
        "meals": [
            random.choice(STATIC_MEALS["Breakfast"]),
            random.choice(STATIC_MEALS["Lunch"]),
            random.choice(STATIC_MEALS["Dinner"]),
        ],
    }
