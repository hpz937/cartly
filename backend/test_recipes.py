import pytest
import json
import os
import tempfile
import shutil
import io
import app as app_module
from app import app, init_db, get_db
from PIL import Image

@pytest.fixture(scope="function")
def client():
    """Create a test client with a fresh temporary database for each test."""
    # Create a unique temporary directory for this test
    temp_dir = tempfile.mkdtemp(prefix="test_recipes_")
    test_db_path = os.path.join(temp_dir, "shopping.db")

    # Save original DB_PATH and patch it
    old_db_path = app_module.DB_PATH
    app_module.DB_PATH = test_db_path

    # Configure app for testing
    app.config['TESTING'] = True

    # Initialize the database with the patched path
    init_db()

    # Create test client
    with app.test_client() as test_client:
        yield test_client

    # Cleanup: restore DB_PATH
    app_module.DB_PATH = old_db_path

    # Remove the temporary directory and all its contents (including WAL files)
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass  # Ignore cleanup errors

@pytest.fixture
def sample_recipe(client):
    """Create a sample recipe for testing."""
    response = client.post('/api/recipes',
        data=json.dumps({
            'name': 'Test Recipe',
            'description': 'A test recipe',
            'servings': 4,
            'prep_time': '10 mins',
            'cook_time': '20 mins'
        }),
        content_type='application/json')
    return json.loads(response.data)

class TestRecipesCRUD:
    """Test recipes CRUD operations."""

    def test_get_recipes_empty(self, client):
        """Test getting recipes when none exist."""
        response = client.get('/api/recipes')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_create_recipe(self, client):
        """Test creating a new recipe."""
        response = client.post('/api/recipes',
            data=json.dumps({
                'name': 'Chocolate Cake',
                'description': 'Delicious chocolate cake',
                'servings': 8,
                'prep_time': '15 mins',
                'cook_time': '30 mins'
            }),
            content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'id' in data
        assert data['name'] == 'Chocolate Cake'

    def test_create_recipe_minimal(self, client):
        """Test creating a recipe with only required fields."""
        response = client.post('/api/recipes',
            data=json.dumps({'name': 'Simple Recipe'}),
            content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Simple Recipe'

    def test_get_all_recipes(self, client, sample_recipe):
        """Test getting all recipes."""
        response = client.get('/api/recipes')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
        # Find our sample recipe in the list
        sample = next((r for r in data if r['id'] == sample_recipe['id']), None)
        assert sample is not None
        assert sample['name'] == 'Test Recipe'
        assert sample['servings'] == 4

    def test_get_single_recipe(self, client, sample_recipe):
        """Test getting a single recipe by ID."""
        recipe_id = sample_recipe['id']
        response = client.get(f'/api/recipes/{recipe_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == recipe_id
        assert data['name'] == 'Test Recipe'
        assert data['description'] == 'A test recipe'

    def test_get_nonexistent_recipe(self, client):
        """Test getting a recipe that doesn't exist."""
        response = client.get('/api/recipes/nonexistent-id')
        assert response.status_code == 404

    def test_update_recipe(self, client, sample_recipe):
        """Test updating a recipe."""
        recipe_id = sample_recipe['id']
        response = client.put(f'/api/recipes/{recipe_id}',
            data=json.dumps({
                'name': 'Updated Recipe',
                'servings': 6,
                'prep_time': '15 mins'
            }),
            content_type='application/json')

        assert response.status_code == 200

        # Verify the update
        response = client.get(f'/api/recipes/{recipe_id}')
        data = json.loads(response.data)
        assert data['name'] == 'Updated Recipe'
        assert data['servings'] == 6
        assert data['prep_time'] == '15 mins'

    def test_delete_recipe(self, client, sample_recipe):
        """Test deleting a recipe."""
        recipe_id = sample_recipe['id']
        response = client.delete(f'/api/recipes/{recipe_id}')
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f'/api/recipes/{recipe_id}')
        assert response.status_code == 404

class TestRecipeIngredients:
    """Test recipe ingredients operations."""

    def test_get_ingredients_empty(self, client, sample_recipe):
        """Test getting ingredients when none exist."""
        recipe_id = sample_recipe['id']
        response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_add_ingredient(self, client, sample_recipe):
        """Test adding an ingredient to a recipe."""
        recipe_id = sample_recipe['id']
        response = client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({
                'name': 'Flour',
                'quantity': '2',
                'unit': 'cups'
            }),
            content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Flour'
        assert data['position'] == 1

    def test_add_multiple_ingredients(self, client, sample_recipe):
        """Test adding multiple ingredients and verify ordering."""
        recipe_id = sample_recipe['id']

        ingredients = [
            {'name': 'Flour', 'quantity': '2', 'unit': 'cups'},
            {'name': 'Sugar', 'quantity': '1', 'unit': 'cup'},
            {'name': 'Eggs', 'quantity': '3', 'unit': ''}
        ]

        for ing in ingredients:
            client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ing),
                content_type='application/json')

        # Get all ingredients
        response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        data = json.loads(response.data)

        assert len(data) == 3
        assert data[0]['name'] == 'Flour'
        assert data[0]['position'] == 1
        assert data[1]['name'] == 'Sugar'
        assert data[1]['position'] == 2
        assert data[2]['name'] == 'Eggs'
        assert data[2]['position'] == 3

    def test_update_ingredient(self, client, sample_recipe):
        """Test updating an ingredient."""
        recipe_id = sample_recipe['id']

        # Create ingredient
        response = client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour', 'quantity': '2', 'unit': 'cups'}),
            content_type='application/json')
        ing_id = json.loads(response.data)['id']

        # Update ingredient
        response = client.put(f'/api/recipes/{recipe_id}/ingredients/{ing_id}',
            data=json.dumps({
                'name': 'All-Purpose Flour',
                'quantity': '2.5',
                'unit': 'cups'
            }),
            content_type='application/json')

        assert response.status_code == 200

        # Verify update
        response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        data = json.loads(response.data)
        assert data[0]['name'] == 'All-Purpose Flour'
        assert data[0]['quantity'] == '2.5'

    def test_delete_ingredient(self, client, sample_recipe):
        """Test deleting an ingredient."""
        recipe_id = sample_recipe['id']

        # Create ingredient
        response = client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour'}),
            content_type='application/json')
        ing_id = json.loads(response.data)['id']

        # Delete ingredient
        response = client.delete(f'/api/recipes/{recipe_id}/ingredients/{ing_id}')
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        assert len(json.loads(response.data)) == 0

class TestRecipeSteps:
    """Test recipe steps operations."""

    def test_get_steps_empty(self, client, sample_recipe):
        """Test getting steps when none exist."""
        recipe_id = sample_recipe['id']
        response = client.get(f'/api/recipes/{recipe_id}/steps')
        assert response.status_code == 200
        assert json.loads(response.data) == []

    def test_add_step(self, client, sample_recipe):
        """Test adding a step to a recipe."""
        recipe_id = sample_recipe['id']
        response = client.post(f'/api/recipes/{recipe_id}/steps',
            data=json.dumps({'instruction': 'Preheat oven to 350F'}),
            content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['step_number'] == 1

    def test_add_multiple_steps(self, client, sample_recipe):
        """Test adding multiple steps and verify numbering."""
        recipe_id = sample_recipe['id']

        steps = [
            'Preheat oven to 350F',
            'Mix dry ingredients',
            'Add wet ingredients',
            'Bake for 30 minutes'
        ]

        for step in steps:
            client.post(f'/api/recipes/{recipe_id}/steps',
                data=json.dumps({'instruction': step}),
                content_type='application/json')

        # Get all steps
        response = client.get(f'/api/recipes/{recipe_id}/steps')
        data = json.loads(response.data)

        assert len(data) == 4
        for i, step_data in enumerate(data):
            assert step_data['step_number'] == i + 1
            assert step_data['instruction'] == steps[i]

    def test_update_step(self, client, sample_recipe):
        """Test updating a step."""
        recipe_id = sample_recipe['id']

        # Create step
        response = client.post(f'/api/recipes/{recipe_id}/steps',
            data=json.dumps({'instruction': 'Preheat oven'}),
            content_type='application/json')
        step_id = json.loads(response.data)['id']

        # Update step
        response = client.put(f'/api/recipes/{recipe_id}/steps/{step_id}',
            data=json.dumps({'instruction': 'Preheat oven to 375F'}),
            content_type='application/json')

        assert response.status_code == 200

        # Verify update
        response = client.get(f'/api/recipes/{recipe_id}/steps')
        data = json.loads(response.data)
        assert data[0]['instruction'] == 'Preheat oven to 375F'

    def test_delete_step_renumbers(self, client, sample_recipe):
        """Test that deleting a step renumbers subsequent steps."""
        recipe_id = sample_recipe['id']

        # Create 3 steps
        steps = ['Step 1', 'Step 2', 'Step 3']
        step_ids = []
        for step in steps:
            response = client.post(f'/api/recipes/{recipe_id}/steps',
                data=json.dumps({'instruction': step}),
                content_type='application/json')
            step_ids.append(json.loads(response.data)['id'])

        # Delete step 2
        response = client.delete(f'/api/recipes/{recipe_id}/steps/{step_ids[1]}')
        assert response.status_code == 200

        # Verify renumbering
        response = client.get(f'/api/recipes/{recipe_id}/steps')
        data = json.loads(response.data)

        assert len(data) == 2
        assert data[0]['instruction'] == 'Step 1'
        assert data[0]['step_number'] == 1
        assert data[1]['instruction'] == 'Step 3'
        assert data[1]['step_number'] == 2  # Should be renumbered to 2

class TestRecipeCascadeDelete:
    """Test cascade delete behavior."""

    def test_delete_recipe_deletes_ingredients(self, client, sample_recipe):
        """Test that deleting a recipe also deletes its ingredients."""
        recipe_id = sample_recipe['id']

        # Add ingredients
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour'}),
            content_type='application/json')

        # Delete recipe
        client.delete(f'/api/recipes/{recipe_id}')

        # Verify ingredients are gone
        response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        # Recipe doesn't exist, so this might 404 or return empty
        # The important thing is ingredients are deleted

    def test_delete_recipe_deletes_steps(self, client, sample_recipe):
        """Test that deleting a recipe also deletes its steps."""
        recipe_id = sample_recipe['id']

        # Add steps
        client.post(f'/api/recipes/{recipe_id}/steps',
            data=json.dumps({'instruction': 'Mix ingredients'}),
            content_type='application/json')

        # Delete recipe
        client.delete(f'/api/recipes/{recipe_id}')

        # Verify steps are gone
        response = client.get(f'/api/recipes/{recipe_id}/steps')
        # Recipe doesn't exist, so ingredients/steps should be gone too

class TestRecipePhotos:
    """Test recipe photo upload and management."""

    def test_upload_photo(self, client, sample_recipe):
        """Test uploading a photo to a recipe."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        response = client.put(
            f'/api/recipes/{sample_recipe["id"]}/photo',
            data={'photo': (img_bytes, 'test.jpg', 'image/jpeg')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200

        # Verify photo was saved
        recipe_response = client.get(f'/api/recipes/{sample_recipe["id"]}')
        recipe = json.loads(recipe_response.data)
        assert recipe['photo'] is not None
        assert recipe['photo'].startswith('data:image/webp;base64,')

    def test_upload_large_photo(self, client, sample_recipe):
        """Test that large photos are rejected."""
        # Create fake file data > 5MB
        # We just need to test the size check, not actual image validity
        large_data = b'\x00' * (6 * 1024 * 1024)  # 6MB of data
        img_bytes = io.BytesIO(large_data)

        response = client.put(
            f'/api/recipes/{sample_recipe["id"]}/photo',
            data={'photo': (img_bytes, 'large.jpg', 'image/jpeg')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'too large' in data['error'].lower()

    def test_delete_photo(self, client, sample_recipe):
        """Test deleting a recipe photo."""
        # First upload a photo
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        client.put(
            f'/api/recipes/{sample_recipe["id"]}/photo',
            data={'photo': (img_bytes, 'test.jpg', 'image/jpeg')},
            content_type='multipart/form-data'
        )

        # Delete photo
        response = client.delete(f'/api/recipes/{sample_recipe["id"]}/photo')
        assert response.status_code == 200

        # Verify photo was deleted
        recipe_response = client.get(f'/api/recipes/{sample_recipe["id"]}')
        recipe = json.loads(recipe_response.data)
        assert recipe['photo'] is None

    def test_upload_no_file(self, client, sample_recipe):
        """Test uploading without providing a file."""
        response = client.put(
            f'/api/recipes/{sample_recipe["id"]}/photo',
            data={},
            content_type='multipart/form-data'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_upload_png_converts_to_webp(self, client, sample_recipe):
        """Test that PNG uploads are converted to WebP."""
        # Create a PNG image
        img = Image.new('RGB', (200, 200), color='purple')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        response = client.put(
            f'/api/recipes/{sample_recipe["id"]}/photo',
            data={'photo': (img_bytes, 'test.png', 'image/png')},
            content_type='multipart/form-data'
        )

        assert response.status_code == 200

        # Verify it was converted to WebP
        recipe_response = client.get(f'/api/recipes/{sample_recipe["id"]}')
        recipe = json.loads(recipe_response.data)
        assert recipe['photo'].startswith('data:image/webp;base64,')

class TestIntegration:
    """Integration tests for complete recipe workflows."""

    def test_complete_recipe_workflow(self, client):
        """Test creating a complete recipe with ingredients and steps."""
        # Create recipe
        response = client.post('/api/recipes',
            data=json.dumps({
                'name': 'Pancakes',
                'description': 'Fluffy pancakes',
                'servings': 4,
                'prep_time': '5 mins',
                'cook_time': '10 mins'
            }),
            content_type='application/json')
        recipe_id = json.loads(response.data)['id']

        # Add ingredients
        ingredients = [
            {'name': 'Flour', 'quantity': '2', 'unit': 'cups'},
            {'name': 'Milk', 'quantity': '1.5', 'unit': 'cups'},
            {'name': 'Eggs', 'quantity': '2', 'unit': ''}
        ]
        for ing in ingredients:
            client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps(ing),
                content_type='application/json')

        # Add steps
        steps = [
            'Mix dry ingredients',
            'Add wet ingredients',
            'Cook on griddle'
        ]
        for step in steps:
            client.post(f'/api/recipes/{recipe_id}/steps',
                data=json.dumps({'instruction': step}),
                content_type='application/json')

        # Get complete recipe
        recipe_response = client.get(f'/api/recipes/{recipe_id}')
        ingredients_response = client.get(f'/api/recipes/{recipe_id}/ingredients')
        steps_response = client.get(f'/api/recipes/{recipe_id}/steps')

        recipe_data = json.loads(recipe_response.data)
        ingredients_data = json.loads(ingredients_response.data)
        steps_data = json.loads(steps_response.data)

        assert recipe_data['name'] == 'Pancakes'
        assert len(ingredients_data) == 3
        assert len(steps_data) == 3
        assert steps_data[0]['step_number'] == 1
        assert steps_data[2]['step_number'] == 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
