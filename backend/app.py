import sqlite3, os, json, uuid, io, base64
from flask import Flask, request, jsonify, g
from datetime import datetime
from PIL import Image

app = Flask(__name__)
DB_PATH = os.path.join(os.environ.get("DB_DIR", "/app/data"), "shopping.db")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db:
        db.close()

def process_recipe_photo(file_data, max_width=800):
    """
    Process uploaded image: resize and convert to WebP base64.

    Args:
        file_data: File bytes from upload
        max_width: Maximum width in pixels (default 800)

    Returns:
        Base64-encoded WebP image with data URI prefix
    """
    # Open image
    image = Image.open(io.BytesIO(file_data))

    # Convert RGBA to RGB if needed
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background

    # Resize maintaining aspect ratio
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

    # Convert to WebP
    output = io.BytesIO()
    image.save(output, format='WEBP', quality=85)
    webp_data = output.getvalue()

    # Encode to base64 with data URI
    b64_string = base64.b64encode(webp_data).decode('utf-8')
    return f"data:image/webp;base64,{b64_string}"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS lists (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            created    TEXT NOT NULL DEFAULT (datetime('now')),
            is_default INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS categories (
            id        TEXT PRIMARY KEY,
            list_id   TEXT NOT NULL,
            name      TEXT NOT NULL,
            position  INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(list_id) REFERENCES lists(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS items (
            id         TEXT PRIMARY KEY,
            list_id    TEXT NOT NULL,
            category   TEXT,
            name       TEXT NOT NULL,
            quantity   TEXT DEFAULT '1',
            note       TEXT DEFAULT '',
            done       INTEGER NOT NULL DEFAULT 0,
            position   INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(list_id) REFERENCES lists(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS recipes (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            servings    INTEGER DEFAULT 4,
            prep_time   TEXT DEFAULT '',
            cook_time   TEXT DEFAULT '',
            photo       TEXT DEFAULT NULL,
            created     TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id          TEXT PRIMARY KEY,
            recipe_id   TEXT NOT NULL,
            name        TEXT NOT NULL,
            quantity    TEXT DEFAULT '',
            unit        TEXT DEFAULT '',
            position    INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS recipe_steps (
            id          TEXT PRIMARY KEY,
            recipe_id   TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            instruction TEXT NOT NULL,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Lists CRUD
# ---------------------------------------------------------------------------
@app.route("/api/lists", methods=["GET"])
def get_lists():
    rows = get_db().execute("SELECT * FROM lists ORDER BY created DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/lists", methods=["POST"])
def create_list():
    data = request.get_json()
    id_ = str(uuid.uuid4())
    get_db().execute("INSERT INTO lists (id, name) VALUES (?, ?)", (id_, data["name"]))
    get_db().commit()
    return jsonify({"id": id_, "name": data["name"]}), 201

@app.route("/api/lists/<list_id>", methods=["PUT"])
def update_list(list_id):
    data = request.get_json()
    get_db().execute("UPDATE lists SET name=? WHERE id=?", (data["name"], list_id))
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/lists/<list_id>", methods=["DELETE"])
def delete_list(list_id):
    get_db().execute("DELETE FROM lists WHERE id=?", (list_id,))
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/lists/<list_id>/set-default", methods=["POST"])
def set_default_list(list_id):
    """Set a list as the default shopping list. Only one list can be default at a time."""
    db = get_db()

    # Verify list exists
    list_row = db.execute("SELECT id FROM lists WHERE id=?", (list_id,)).fetchone()
    if not list_row:
        return jsonify({"error": "List not found"}), 404

    # Atomic operation: unset all defaults, then set the new one
    db.execute("UPDATE lists SET is_default = 0")
    db.execute("UPDATE lists SET is_default = 1 WHERE id=?", (list_id,))
    db.commit()

    return jsonify({"ok": True, "default_list_id": list_id})

@app.route("/api/lists/default", methods=["GET"])
def get_default_list():
    """Get the current default shopping list."""
    row = get_db().execute("SELECT * FROM lists WHERE is_default = 1").fetchone()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "No default list set"}), 404

# ---------------------------------------------------------------------------
# Recipes CRUD
# ---------------------------------------------------------------------------
@app.route("/api/recipes", methods=["GET"])
def get_recipes():
    rows = get_db().execute("SELECT * FROM recipes ORDER BY created DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/recipes", methods=["POST"])
def create_recipe():
    data = request.get_json()
    id_ = str(uuid.uuid4())
    get_db().execute(
        "INSERT INTO recipes (id, name, description, servings, prep_time, cook_time) VALUES (?, ?, ?, ?, ?, ?)",
        (id_, data["name"], data.get("description", ""), data.get("servings", 4),
         data.get("prep_time", ""), data.get("cook_time", ""))
    )
    get_db().commit()
    return jsonify({"id": id_, "name": data["name"]}), 201

@app.route("/api/recipes/<recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    row = get_db().execute("SELECT * FROM recipes WHERE id=?", (recipe_id,)).fetchone()
    if row:
        return jsonify(dict(row))
    return jsonify({"error": "Not found"}), 404

@app.route("/api/recipes/<recipe_id>", methods=["PUT"])
def update_recipe(recipe_id):
    data = request.get_json()
    db = get_db()
    sets = []
    vals = []
    for k in ("name", "description", "servings", "prep_time", "cook_time"):
        if k in data:
            sets.append(f"{k}=?")
            vals.append(data[k])
    if sets:
        vals.append(recipe_id)
        db.execute(f"UPDATE recipes SET {','.join(sets)} WHERE id=?", vals)
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/recipes/<recipe_id>", methods=["DELETE"])
def delete_recipe(recipe_id):
    get_db().execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/recipes/<recipe_id>/photo", methods=["PUT"])
def upload_recipe_photo(recipe_id):
    """Upload and process a recipe photo."""
    # Check if file is present
    if 'photo' not in request.files:
        return jsonify({"error": "No photo file provided"}), 400

    file = request.files['photo']

    # Check file size (5MB limit)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to start

    if size > 5 * 1024 * 1024:  # 5MB
        return jsonify({"error": "File too large (max 5MB)"}), 400

    # Check file type
    if not file.content_type or not file.content_type.startswith('image/'):
        return jsonify({"error": "File must be an image"}), 400

    try:
        # Process image
        file_data = file.read()
        photo_data = process_recipe_photo(file_data)

        # Update database
        get_db().execute(
            "UPDATE recipes SET photo=? WHERE id=?",
            (photo_data, recipe_id)
        )
        get_db().commit()

        return jsonify({"ok": True, "message": "Photo uploaded successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/recipes/<recipe_id>/photo", methods=["DELETE"])
def delete_recipe_photo(recipe_id):
    """Delete a recipe photo."""
    get_db().execute(
        "UPDATE recipes SET photo=NULL WHERE id=?",
        (recipe_id,)
    )
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/recipes/<recipe_id>/add-to-shopping-list", methods=["POST"])
def add_recipe_to_shopping_list(recipe_id):
    """Add all ingredients from a recipe to the default shopping list.

    Handles duplicate detection (case-insensitive) and quantity formatting.
    Returns summary of added/skipped items.
    """
    db = get_db()

    # 1. Get default list
    default_list = db.execute("SELECT id FROM lists WHERE is_default = 1").fetchone()
    if not default_list:
        return jsonify({
            "error": "No default list set",
            "message": "Please set a default shopping list first"
        }), 400

    list_id = default_list["id"]

    # 2. Get recipe ingredients
    ingredients = db.execute(
        "SELECT name, quantity, unit FROM recipe_ingredients WHERE recipe_id=? ORDER BY position",
        (recipe_id,)
    ).fetchall()

    if not ingredients:
        return jsonify({
            "error": "No ingredients found",
            "message": "This recipe has no ingredients to add"
        }), 400

    # 3. Get existing items for duplicate detection
    existing_items = db.execute("SELECT name FROM items WHERE list_id=?", (list_id,)).fetchall()
    existing_names_lower = {item["name"].lower() for item in existing_items}

    # 4. Add ingredients (skip duplicates)
    added = []
    skipped = []

    for ing in ingredients:
        ing_name = ing["name"]

        # Check for duplicate (case-insensitive)
        if ing_name.lower() in existing_names_lower:
            skipped.append(ing_name)
            continue

        # Format quantity: "quantity unit" or just quantity if no unit
        quantity_parts = [ing["quantity"], ing["unit"]]
        formatted_qty = " ".join(filter(None, quantity_parts)) or "1"

        # Get next position for uncategorized items
        pos = db.execute(
            "SELECT COALESCE(MAX(position),0)+1 as p FROM items WHERE list_id=? AND category IS NULL",
            (list_id,)
        ).fetchone()["p"]

        # Insert the item
        item_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO items (id, list_id, category, name, quantity, note, done, position) VALUES (?,?,NULL,?,?,'',0,?)",
            (item_id, list_id, ing_name, formatted_qty, pos)
        )

        added.append(ing_name)
        existing_names_lower.add(ing_name.lower())  # Prevent intra-recipe duplicates

    db.commit()

    return jsonify({
        "ok": True,
        "list_id": list_id,
        "added_count": len(added),
        "skipped_count": len(skipped),
        "added": added,
        "skipped": skipped,
        "message": f"Added {len(added)} ingredient(s) to your shopping list" +
                   (f" ({len(skipped)} duplicate(s) skipped)" if skipped else "")
    })

@app.route("/api/recipes/<recipe_id>/ingredients/<ingredient_id>/add-to-shopping-list", methods=["POST"])
def add_ingredient_to_shopping_list(recipe_id, ingredient_id):
    """Add a single ingredient from a recipe to the default shopping list.

    Handles duplicate detection (case-insensitive) and quantity formatting.
    """
    db = get_db()

    # 1. Get default list
    default_list = db.execute("SELECT id FROM lists WHERE is_default = 1").fetchone()
    if not default_list:
        return jsonify({
            "error": "No default list set",
            "message": "Please set a default shopping list first"
        }), 400

    list_id = default_list["id"]

    # 2. Get the specific ingredient
    ingredient = db.execute(
        "SELECT name, quantity, unit FROM recipe_ingredients WHERE id=? AND recipe_id=?",
        (ingredient_id, recipe_id)
    ).fetchone()

    if not ingredient:
        return jsonify({
            "error": "Ingredient not found"
        }), 404

    # 3. Check for duplicate (case-insensitive)
    existing_items = db.execute("SELECT name FROM items WHERE list_id=?", (list_id,)).fetchall()
    existing_names_lower = {item["name"].lower() for item in existing_items}

    ing_name = ingredient["name"]

    if ing_name.lower() in existing_names_lower:
        return jsonify({
            "ok": False,
            "skipped": True,
            "message": f"'{ing_name}' is already in your shopping list"
        })

    # 4. Format quantity and add to list
    quantity_parts = [ingredient["quantity"], ingredient["unit"]]
    formatted_qty = " ".join(filter(None, quantity_parts)) or "1"

    # Get next position for uncategorized items
    pos = db.execute(
        "SELECT COALESCE(MAX(position),0)+1 as p FROM items WHERE list_id=? AND category IS NULL",
        (list_id,)
    ).fetchone()["p"]

    # Insert the item
    item_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO items (id, list_id, category, name, quantity, note, done, position) VALUES (?,?,NULL,?,?,'',0,?)",
        (item_id, list_id, ing_name, formatted_qty, pos)
    )
    db.commit()

    return jsonify({
        "ok": True,
        "list_id": list_id,
        "message": f"Added '{ing_name}' to your shopping list"
    })

# ---------------------------------------------------------------------------
# Recipe Ingredients CRUD
# ---------------------------------------------------------------------------
@app.route("/api/recipes/<recipe_id>/ingredients", methods=["GET"])
def get_recipe_ingredients(recipe_id):
    rows = get_db().execute(
        "SELECT * FROM recipe_ingredients WHERE recipe_id=? ORDER BY position", (recipe_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/recipes/<recipe_id>/ingredients", methods=["POST"])
def create_recipe_ingredient(recipe_id):
    data = request.get_json()
    id_ = str(uuid.uuid4())
    pos = get_db().execute(
        "SELECT COALESCE(MAX(position),0)+1 as p FROM recipe_ingredients WHERE recipe_id=?", (recipe_id,)
    ).fetchone()["p"]
    get_db().execute(
        "INSERT INTO recipe_ingredients (id, recipe_id, name, quantity, unit, position) VALUES (?,?,?,?,?,?)",
        (id_, recipe_id, data["name"], data.get("quantity", ""), data.get("unit", ""), pos)
    )
    get_db().commit()
    return jsonify({"id": id_, "name": data["name"], "position": pos}), 201

@app.route("/api/recipes/<recipe_id>/ingredients/<ing_id>", methods=["PUT"])
def update_recipe_ingredient(recipe_id, ing_id):
    data = request.get_json()
    db = get_db()
    sets = []
    vals = []
    for k in ("name", "quantity", "unit"):
        if k in data:
            sets.append(f"{k}=?")
            vals.append(data[k])
    if sets:
        vals.extend([ing_id, recipe_id])
        db.execute(f"UPDATE recipe_ingredients SET {','.join(sets)} WHERE id=? AND recipe_id=?", vals)
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/recipes/<recipe_id>/ingredients/<ing_id>", methods=["DELETE"])
def delete_recipe_ingredient(recipe_id, ing_id):
    get_db().execute("DELETE FROM recipe_ingredients WHERE id=? AND recipe_id=?", (ing_id, recipe_id))
    get_db().commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Recipe Steps CRUD
# ---------------------------------------------------------------------------
@app.route("/api/recipes/<recipe_id>/steps", methods=["GET"])
def get_recipe_steps(recipe_id):
    rows = get_db().execute(
        "SELECT * FROM recipe_steps WHERE recipe_id=? ORDER BY step_number", (recipe_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/recipes/<recipe_id>/steps", methods=["POST"])
def create_recipe_step(recipe_id):
    data = request.get_json()
    id_ = str(uuid.uuid4())
    step_num = get_db().execute(
        "SELECT COALESCE(MAX(step_number),0)+1 as n FROM recipe_steps WHERE recipe_id=?", (recipe_id,)
    ).fetchone()["n"]
    get_db().execute(
        "INSERT INTO recipe_steps (id, recipe_id, step_number, instruction) VALUES (?,?,?,?)",
        (id_, recipe_id, step_num, data["instruction"])
    )
    get_db().commit()
    return jsonify({"id": id_, "step_number": step_num}), 201

@app.route("/api/recipes/<recipe_id>/steps/<step_id>", methods=["PUT"])
def update_recipe_step(recipe_id, step_id):
    data = request.get_json()
    get_db().execute(
        "UPDATE recipe_steps SET instruction=? WHERE id=? AND recipe_id=?",
        (data["instruction"], step_id, recipe_id)
    )
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/recipes/<recipe_id>/steps/<step_id>", methods=["DELETE"])
def delete_recipe_step(recipe_id, step_id):
    db = get_db()
    # Get the step number being deleted
    deleted_step = db.execute(
        "SELECT step_number FROM recipe_steps WHERE id=? AND recipe_id=?", (step_id, recipe_id)
    ).fetchone()
    # Delete the step
    db.execute("DELETE FROM recipe_steps WHERE id=? AND recipe_id=?", (step_id, recipe_id))
    # Renumber subsequent steps
    if deleted_step:
        db.execute(
            "UPDATE recipe_steps SET step_number = step_number - 1 WHERE recipe_id=? AND step_number > ?",
            (recipe_id, deleted_step["step_number"])
        )
    db.commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Categories CRUD
# ---------------------------------------------------------------------------
@app.route("/api/lists/<list_id>/categories", methods=["GET"])
def get_categories(list_id):
    rows = get_db().execute(
        "SELECT * FROM categories WHERE list_id=? ORDER BY position", (list_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/lists/<list_id>/categories", methods=["POST"])
def create_category(list_id):
    data = request.get_json()
    id_ = str(uuid.uuid4())
    pos = get_db().execute(
        "SELECT COALESCE(MAX(position),0)+1 as p FROM categories WHERE list_id=?", (list_id,)
    ).fetchone()["p"]
    get_db().execute(
        "INSERT INTO categories (id, list_id, name, position) VALUES (?,?,?,?)",
        (id_, list_id, data["name"], pos)
    )
    get_db().commit()
    return jsonify({"id": id_, "name": data["name"], "position": pos}), 201

@app.route("/api/lists/<list_id>/categories/<cat_id>", methods=["PUT"])
def update_category(list_id, cat_id):
    data = request.get_json()
    get_db().execute("UPDATE categories SET name=? WHERE id=? AND list_id=?", (data["name"], cat_id, list_id))
    get_db().commit()
    return jsonify({"ok": True})

@app.route("/api/lists/<list_id>/categories/<cat_id>", methods=["DELETE"])
def delete_category(list_id, cat_id):
    # move items to uncategorised
    get_db().execute("UPDATE items SET category=NULL WHERE category=? AND list_id=?", (cat_id, list_id))
    get_db().execute("DELETE FROM categories WHERE id=? AND list_id=?", (cat_id, list_id))
    get_db().commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Items CRUD
# ---------------------------------------------------------------------------
@app.route("/api/lists/<list_id>/items", methods=["GET"])
def get_items(list_id):
    rows = get_db().execute(
        "SELECT * FROM items WHERE list_id=? ORDER BY category, position", (list_id,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/lists/<list_id>/items", methods=["POST"])
def create_item(list_id):
    data = request.get_json()
    id_ = str(uuid.uuid4())
    cat = data.get("category")
    pos = get_db().execute(
        "SELECT COALESCE(MAX(position),0)+1 as p FROM items WHERE list_id=? AND category IS ?",
        (list_id, cat)
    ).fetchone()["p"]
    get_db().execute(
        "INSERT INTO items (id, list_id, category, name, quantity, note, done, position) VALUES (?,?,?,?,?,?,0,?)",
        (id_, list_id, cat, data["name"], data.get("quantity","1"), data.get("note",""), pos)
    )
    get_db().commit()
    return jsonify({"id": id_}), 201

@app.route("/api/lists/<list_id>/items/<item_id>", methods=["PUT"])
def update_item(list_id, item_id):
    data = request.get_json()
    db = get_db()
    sets = []
    vals = []
    for k in ("name", "quantity", "note", "category"):
        if k in data:
            sets.append(f"{k}=?")
            vals.append(data[k])
    if sets:
        vals.extend([item_id, list_id])
        db.execute(f"UPDATE items SET {','.join(sets)} WHERE id=? AND list_id=?", vals)
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/lists/<list_id>/items/<item_id>/toggle", methods=["POST"])
def toggle_item(list_id, item_id):
    db = get_db()
    db.execute(
        "UPDATE items SET done = 1 - done WHERE id=? AND list_id=?", (item_id, list_id)
    )
    db.commit()
    row = db.execute("SELECT done FROM items WHERE id=?", (item_id,)).fetchone()
    return jsonify({"done": row["done"]})

@app.route("/api/lists/<list_id>/items/<item_id>", methods=["DELETE"])
def delete_item(list_id, item_id):
    get_db().execute("DELETE FROM items WHERE id=? AND list_id=?", (item_id, list_id))
    get_db().commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Convenience: clear completed items
# ---------------------------------------------------------------------------
@app.route("/api/lists/<list_id>/items/clear-done", methods=["DELETE"])
def clear_done(list_id):
    get_db().execute("DELETE FROM items WHERE list_id=? AND done=1", (list_id,))
    get_db().commit()
    return jsonify({"ok": True})

# ---------------------------------------------------------------------------
# Stats helper (used by the UI header)
# ---------------------------------------------------------------------------
@app.route("/api/lists/<list_id>/stats", methods=["GET"])
def get_stats(list_id):
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM items WHERE list_id=?", (list_id,)).fetchone()["c"]
    done  = db.execute("SELECT COUNT(*) as c FROM items WHERE list_id=? AND done=1", (list_id,)).fetchone()["c"]
    return jsonify({"total": total, "done": done})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

# gunicorn calls this automatically
init_db()
