#!/usr/bin/env python3
"""Add sample recipes to the database for testing."""

import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.environ.get("DB_DIR", "/app/data"), "shopping.db")

SAMPLE_RECIPES = [
    {
        "name": "Classic Chocolate Chip Cookies",
        "description": "Soft and chewy chocolate chip cookies that everyone loves",
        "servings": 24,
        "prep_time": "15 mins",
        "cook_time": "12 mins",
        "ingredients": [
            {"name": "All-purpose flour", "quantity": "2¼", "unit": "cups"},
            {"name": "Butter", "quantity": "1", "unit": "cup"},
            {"name": "Granulated sugar", "quantity": "¾", "unit": "cup"},
            {"name": "Brown sugar", "quantity": "¾", "unit": "cup"},
            {"name": "Eggs", "quantity": "2", "unit": ""},
            {"name": "Vanilla extract", "quantity": "2", "unit": "tsp"},
            {"name": "Baking soda", "quantity": "1", "unit": "tsp"},
            {"name": "Salt", "quantity": "1", "unit": "tsp"},
            {"name": "Chocolate chips", "quantity": "2", "unit": "cups"},
        ],
        "steps": [
            "Preheat oven to 375°F (190°C)",
            "Mix butter and sugars until creamy",
            "Beat in eggs and vanilla",
            "Combine flour, baking soda, and salt in separate bowl",
            "Gradually blend dry ingredients into butter mixture",
            "Stir in chocolate chips",
            "Drop rounded tablespoons onto ungreased cookie sheets",
            "Bake 9-11 minutes or until golden brown",
            "Cool on baking sheet for 2 minutes, then move to wire rack",
        ]
    },
    {
        "name": "Homemade Pizza",
        "description": "Delicious homemade pizza with fresh toppings",
        "servings": 4,
        "prep_time": "2 hours",
        "cook_time": "15 mins",
        "ingredients": [
            {"name": "Warm water", "quantity": "1", "unit": "cup"},
            {"name": "Active dry yeast", "quantity": "1", "unit": "packet"},
            {"name": "All-purpose flour", "quantity": "3", "unit": "cups"},
            {"name": "Olive oil", "quantity": "2", "unit": "tbsp"},
            {"name": "Salt", "quantity": "1", "unit": "tsp"},
            {"name": "Sugar", "quantity": "1", "unit": "tsp"},
            {"name": "Pizza sauce", "quantity": "1", "unit": "cup"},
            {"name": "Mozzarella cheese", "quantity": "2", "unit": "cups"},
            {"name": "Toppings of choice", "quantity": "", "unit": ""},
        ],
        "steps": [
            "Dissolve yeast in warm water with sugar, let stand 5 minutes",
            "Mix flour and salt in large bowl",
            "Add yeast mixture and olive oil, stir to combine",
            "Knead dough on floured surface for 5 minutes",
            "Place in greased bowl, cover, let rise 1 hour",
            "Preheat oven to 475°F (245°C)",
            "Roll out dough on floured surface to desired thickness",
            "Transfer to pizza pan or baking sheet",
            "Spread sauce, add cheese and toppings",
            "Bake 12-15 minutes until crust is golden and cheese is bubbly",
        ]
    },
    {
        "name": "Caesar Salad",
        "description": "Fresh Caesar salad with homemade dressing",
        "servings": 4,
        "prep_time": "15 mins",
        "cook_time": "0 mins",
        "ingredients": [
            {"name": "Romaine lettuce", "quantity": "1", "unit": "head"},
            {"name": "Garlic", "quantity": "2", "unit": "cloves"},
            {"name": "Anchovy fillets", "quantity": "4", "unit": ""},
            {"name": "Lemon juice", "quantity": "2", "unit": "tbsp"},
            {"name": "Dijon mustard", "quantity": "1", "unit": "tsp"},
            {"name": "Olive oil", "quantity": "½", "unit": "cup"},
            {"name": "Parmesan cheese", "quantity": "½", "unit": "cup"},
            {"name": "Croutons", "quantity": "1", "unit": "cup"},
        ],
        "steps": [
            "Wash and dry romaine lettuce, tear into bite-sized pieces",
            "Mince garlic and anchovies into a paste",
            "Whisk together garlic paste, lemon juice, and mustard",
            "Slowly drizzle in olive oil while whisking",
            "Toss lettuce with dressing",
            "Add grated Parmesan and croutons",
            "Serve immediately",
        ]
    }
]

def add_sample_recipes():
    """Add sample recipes to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check how many recipes exist
    cursor.execute("SELECT COUNT(*) FROM recipes")
    existing_count = cursor.fetchone()[0]

    print(f"Current database has {existing_count} recipe(s)")
    print(f"\nAdding {len(SAMPLE_RECIPES)} sample recipes...\n")

    for recipe_data in SAMPLE_RECIPES:
        recipe_id = str(uuid.uuid4())

        # Insert recipe
        cursor.execute(
            """INSERT INTO recipes (id, name, description, servings, prep_time, cook_time, created)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (recipe_id, recipe_data["name"], recipe_data["description"],
             recipe_data["servings"], recipe_data["prep_time"], recipe_data["cook_time"],
             datetime.now().isoformat())
        )

        print(f"✓ Added recipe: {recipe_data['name']}")

        # Insert ingredients
        for idx, ing in enumerate(recipe_data["ingredients"], 1):
            ing_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, position)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (ing_id, recipe_id, ing["name"], ing["quantity"], ing["unit"], idx)
            )
        print(f"  Added {len(recipe_data['ingredients'])} ingredients")

        # Insert steps
        for idx, step in enumerate(recipe_data["steps"], 1):
            step_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO recipe_steps (id, recipe_id, step_number, instruction)
                   VALUES (?, ?, ?, ?)""",
                (step_id, recipe_id, idx, step)
            )
        print(f"  Added {len(recipe_data['steps'])} steps\n")

    conn.commit()

    # Final count
    cursor.execute("SELECT COUNT(*) FROM recipes")
    final_count = cursor.fetchone()[0]

    print(f"✓ Successfully added sample recipes!")
    print(f"Database now has {final_count} recipe(s) total")

    conn.close()

if __name__ == "__main__":
    add_sample_recipes()
