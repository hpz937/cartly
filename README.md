# Cartly — Shopping List App

A self-contained, Docker-based shopping list web app.

## Quick Start

```bash
docker compose up -d --build
```

Open **http://localhost:8080** in your browser.

To stop:

```bash
docker compose down
```

## Architecture

| Layer      | Technology          | Role                                      |
|------------|---------------------|-------------------------------------------|
| Frontend   | Alpine.js + Tailwind CSS | Single-page app with reactive components |
| Reverse Proxy | Nginx (Alpine)   | Serves static files, proxies `/api/*`     |
| Backend    | Flask + Gunicorn    | RESTful API, business logic               |
| Database   | SQLite (WAL mode)   | Persistent storage via a Docker volume    |

```
┌─────────┐     ┌───────┐     ┌─────────┐     ┌────────┐
│ Browser │────▶│ Nginx │────▶│  Flask  │────▶│ SQLite │
│ :8080   │     │       │     │  :5000  │     │  WAL   │
└─────────┘     └───────┘     └─────────┘     └────────┘
```

## Features

- **Multiple lists** — create, rename, delete shopping lists
- **Categories** — organise items into groups (Produce, Dairy, etc.)
- **Quick-add** — type an item name + optional quantity and press Enter
- **Check off** — tap the checkbox to mark items done
- **Progress bar** — see how much of your list is complete at a glance
- **Clear done** — remove all completed items in one tap
- **Edit items** — change name, quantity, note, or category
- **Recipes** — create and manage recipes with ingredients, step-by-step instructions, notes, and photos
- **Drag-and-drop reordering** — easily reorder ingredients and steps by dragging them
- **Import/export recipes** — backup, share, and restore recipes in JSON format
- **Default list** — mark one list as your default for quick recipe-to-list workflows
- **Recipe-to-list** — add all ingredients from a recipe to your default shopping list in one tap
- **Smart duplicate detection** — automatically skips items already in your list (case-insensitive)
- **Recipe scaling** — adjust servings with +/- buttons and automatically scale ingredient quantities
- **Search & sort** — quickly find recipes by name or description, sort by name or date
- **Theme-matched modals** — beautiful, consistent dialogs that match the dark theme (no jarring browser popups)
- **Persistent data** — everything survives container restarts (Docker volume)

## Testing

The recipes feature includes a comprehensive test suite with 26 unit tests.

### Running Tests

Install test dependencies:

```bash
cd backend
pip install pytest flask
```

Run all tests:

```bash
python -m pytest test_recipes.py -v
```

Run a specific test:

```bash
python -m pytest test_recipes.py::TestRecipesCRUD::test_create_recipe -v
```

### Test Coverage

The test suite covers:
- **Recipes CRUD**: Creating, reading, updating, and deleting recipes
- **Ingredients**: Adding, updating, deleting, and ordering ingredients
- **Steps**: Adding, updating, deleting, and automatic renumbering of steps
- **Photo Upload**: Uploading photos, size validation, format conversion to WebP, and deletion
- **Cascade Deletes**: Verifying related data is deleted with recipes
- **Integration**: Complete recipe workflow with ingredients and steps

All tests use isolated temporary databases to ensure no interference between tests.

## Development

### Adding Sample Recipes

To populate your database with sample recipes for testing:

```bash
docker compose cp backend/add_sample_recipes.py backend:/app/
docker compose exec backend python add_sample_recipes.py
```

This adds 3 sample recipes:
- Classic Chocolate Chip Cookies
- Homemade Pizza
- Caesar Salad

### Database Migrations

**For the default list feature:**

If you're upgrading from an earlier version without the `is_default` column:

```bash
docker compose cp backend/migrate_add_default.py backend:/app/
docker compose exec backend python migrate_add_default.py
```

This safely adds the `is_default` column to the lists table without losing data. If you have exactly one list, it will automatically be set as the default.

**For the photo feature:**

If you're upgrading from an earlier version without the photo column:

```bash
docker compose cp backend/migrate_add_photo.py backend:/app/
docker compose exec backend python migrate_add_photo.py
```

This safely adds the `photo` column to existing recipes without losing data.

**For the notes feature:**

If you're upgrading from an earlier version without the notes column:

```bash
docker compose cp backend/migrate_add_notes.py backend:/app/
docker compose exec backend python migrate_add_notes.py
```

This safely adds the `notes` column to existing recipes without losing data.

## API Reference

### Shopping Lists

| Method | Endpoint                                  | Description                 |
|--------|-------------------------------------------|-----------------------------|
| GET    | `/api/lists`                              | List all shopping lists     |
| POST   | `/api/lists`                              | Create a list               |
| PUT    | `/api/lists/:id`                          | Rename a list               |
| DELETE | `/api/lists/:id`                          | Delete a list               |
| POST   | `/api/lists/:id/set-default`              | Set list as default         |
| GET    | `/api/lists/default`                      | Get the default list        |
| GET    | `/api/lists/:id/categories`               | Get categories              |
| POST   | `/api/lists/:id/categories`               | Create a category           |
| PUT    | `/api/lists/:id/categories/:cid`          | Rename a category           |
| DELETE | `/api/lists/:id/categories/:cid`          | Delete a category           |
| GET    | `/api/lists/:id/items`                    | Get items                   |
| POST   | `/api/lists/:id/items`                    | Add an item                 |
| PUT    | `/api/lists/:id/items/:iid`               | Edit an item                |
| POST   | `/api/lists/:id/items/:iid/toggle`        | Toggle done state           |
| DELETE | `/api/lists/:id/items/:iid`               | Delete an item              |
| DELETE | `/api/lists/:id/items/clear-done`         | Remove all completed items  |

### Recipes

| Method | Endpoint                                  | Description                 |
|--------|-------------------------------------------|-----------------------------|
| GET    | `/api/recipes`                            | List all recipes            |
| POST   | `/api/recipes`                            | Create a recipe             |
| GET    | `/api/recipes/:id`                        | Get a single recipe         |
| PUT    | `/api/recipes/:id`                        | Update a recipe             |
| DELETE | `/api/recipes/:id`                        | Delete a recipe             |
| GET    | `/api/recipes/:id/ingredients`            | Get recipe ingredients      |
| POST   | `/api/recipes/:id/ingredients`            | Add an ingredient           |
| PUT    | `/api/recipes/:id/ingredients/:iid`       | Update an ingredient        |
| DELETE | `/api/recipes/:id/ingredients/:iid`       | Delete an ingredient        |
| PUT    | `/api/recipes/:id/ingredients/reorder`    | Reorder ingredients         |
| GET    | `/api/recipes/:id/steps`                  | Get recipe steps            |
| POST   | `/api/recipes/:id/steps`                  | Add a step                  |
| PUT    | `/api/recipes/:id/steps/:sid`             | Update a step               |
| DELETE | `/api/recipes/:id/steps/:sid`             | Delete a step               |
| PUT    | `/api/recipes/:id/steps/reorder`          | Reorder steps               |
| PUT    | `/api/recipes/:id/photo`                  | Upload a recipe photo       |
| DELETE | `/api/recipes/:id/photo`                  | Delete a recipe photo       |
| POST   | `/api/recipes/:id/add-to-shopping-list`   | Add ingredients to default list |
| GET    | `/api/recipes/:id/export`                 | Export recipe as JSON       |
| GET    | `/api/recipes/export`                     | Export all recipes as JSON  |
| POST   | `/api/recipes/import`                     | Import recipe(s) from JSON  |
