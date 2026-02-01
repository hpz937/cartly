import pytest
import json
import os
import tempfile
import shutil
import app as app_module
from app import app, init_db, get_db


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for the test database."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def client(temp_db_dir, monkeypatch):
    """Create a test client with isolated database."""
    db_path = os.path.join(temp_db_dir, "test.db")
    monkeypatch.setattr(app_module, "DB_PATH", db_path)

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


class TestDefaultList:
    """Test default list functionality."""

    def test_set_default_list(self, client):
        """Test setting a list as default."""
        # Create two lists
        list1 = client.post('/api/lists',
            data=json.dumps({'name': 'List 1'}),
            content_type='application/json')
        list1_id = json.loads(list1.data)['id']

        list2 = client.post('/api/lists',
            data=json.dumps({'name': 'List 2'}),
            content_type='application/json')
        list2_id = json.loads(list2.data)['id']

        # Set list1 as default
        response = client.post(f'/api/lists/{list1_id}/set-default')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['default_list_id'] == list1_id

        # Verify only list1 is default
        lists = json.loads(client.get('/api/lists').data)
        list1_data = next(l for l in lists if l['id'] == list1_id)
        list2_data = next(l for l in lists if l['id'] == list2_id)
        assert list1_data['is_default'] == 1
        assert list2_data['is_default'] == 0

    def test_only_one_default(self, client):
        """Test that setting new default unsets previous."""
        # Create two lists
        list1_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'List 1'}),
            content_type='application/json').data)['id']
        list2_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'List 2'}),
            content_type='application/json').data)['id']

        # Set list1 as default
        client.post(f'/api/lists/{list1_id}/set-default')

        # Set list2 as default
        client.post(f'/api/lists/{list2_id}/set-default')

        # Verify only list2 is default
        lists = json.loads(client.get('/api/lists').data)
        list1_data = next(l for l in lists if l['id'] == list1_id)
        list2_data = next(l for l in lists if l['id'] == list2_id)
        assert list1_data['is_default'] == 0
        assert list2_data['is_default'] == 1

    def test_get_default_list(self, client):
        """Test retrieving the default list."""
        # No default initially
        response = client.get('/api/lists/default')
        assert response.status_code == 404

        # Create and set default
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Default List'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        # Should now return the default list
        response = client.get('/api/lists/default')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == list_id
        assert data['is_default'] == 1

    def test_set_default_nonexistent_list(self, client):
        """Test setting non-existent list as default returns 404."""
        response = client.post('/api/lists/nonexistent-id/set-default')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestRecipeToShoppingList:
    """Test adding recipe ingredients to shopping list."""

    def test_add_recipe_to_shopping_list(self, client):
        """Test adding recipe ingredients to default list."""
        # Create default list
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Shopping'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        # Create recipe with ingredients
        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Test Recipe'}),
            content_type='application/json').data)['id']
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour', 'quantity': '2', 'unit': 'cups'}),
            content_type='application/json')
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Sugar', 'quantity': '1', 'unit': 'cup'}),
            content_type='application/json')

        # Add to shopping list
        response = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['added_count'] == 2
        assert data['skipped_count'] == 0
        assert len(data['added']) == 2
        assert 'Flour' in data['added']
        assert 'Sugar' in data['added']

        # Verify items added with correct quantities
        items = json.loads(client.get(f'/api/lists/{list_id}/items').data)
        assert len(items) == 2
        # Items might be in any order
        flour = next(i for i in items if i['name'] == 'Flour')
        sugar = next(i for i in items if i['name'] == 'Sugar')
        assert flour['quantity'] == '2 cups'
        assert sugar['quantity'] == '1 cup'

    def test_duplicate_detection_case_insensitive(self, client):
        """Test case-insensitive duplicate detection."""
        # Setup
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Shopping'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        # Add "FLOUR" manually
        client.post(f'/api/lists/{list_id}/items',
            data=json.dumps({'name': 'FLOUR', 'quantity': '1 cup'}),
            content_type='application/json')

        # Create recipe with "flour" (different case)
        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Recipe'}),
            content_type='application/json').data)['id']
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'flour', 'quantity': '2', 'unit': 'cups'}),
            content_type='application/json')

        # Add to list
        response = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        data = json.loads(response.data)

        # Should skip duplicate
        assert data['added_count'] == 0
        assert data['skipped_count'] == 1
        assert 'flour' in data['skipped']

        # Verify only 1 item exists (the original)
        items = json.loads(client.get(f'/api/lists/{list_id}/items').data)
        assert len(items) == 1
        assert items[0]['name'] == 'FLOUR'

    def test_no_default_list_error(self, client):
        """Test error when no default list is set."""
        # Create recipe with ingredients
        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Recipe'}),
            content_type='application/json').data)['id']
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour'}),
            content_type='application/json')

        # Try to add to shopping list without default
        response = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'No default list' in data['error']

    def test_quantity_formatting(self, client):
        """Test that quantities are formatted correctly."""
        # Setup
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Shopping'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Recipe'}),
            content_type='application/json').data)['id']

        # Test various quantity formats
        test_cases = [
            {'name': 'Flour', 'quantity': '2', 'unit': 'cups', 'expected': '2 cups'},
            {'name': 'Sugar', 'quantity': '1', 'unit': '', 'expected': '1'},
            {'name': 'Salt', 'quantity': '', 'unit': 'tsp', 'expected': 'tsp'},
            {'name': 'Eggs', 'quantity': '', 'unit': '', 'expected': '1'},
        ]

        for tc in test_cases:
            client.post(f'/api/recipes/{recipe_id}/ingredients',
                data=json.dumps({'name': tc['name'], 'quantity': tc['quantity'], 'unit': tc['unit']}),
                content_type='application/json')

        # Add to list
        client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')

        # Verify formatting
        items = json.loads(client.get(f'/api/lists/{list_id}/items').data)
        assert len(items) == len(test_cases)

        for tc in test_cases:
            item = next(i for i in items if i['name'] == tc['name'])
            assert item['quantity'] == tc['expected'], f"Expected {tc['expected']} for {tc['name']}, got {item['quantity']}"

    def test_empty_recipe_error(self, client):
        """Test error when recipe has no ingredients."""
        # Setup
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Shopping'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        # Create recipe without ingredients
        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Empty Recipe'}),
            content_type='application/json').data)['id']

        # Try to add to shopping list
        response = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'No ingredients found' in data['error']

    def test_add_recipe_twice_skips_all(self, client):
        """Test adding same recipe twice skips all on second attempt."""
        # Setup
        list_id = json.loads(client.post('/api/lists',
            data=json.dumps({'name': 'Shopping'}),
            content_type='application/json').data)['id']
        client.post(f'/api/lists/{list_id}/set-default')

        recipe_id = json.loads(client.post('/api/recipes',
            data=json.dumps({'name': 'Recipe'}),
            content_type='application/json').data)['id']
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Flour', 'quantity': '2', 'unit': 'cups'}),
            content_type='application/json')
        client.post(f'/api/recipes/{recipe_id}/ingredients',
            data=json.dumps({'name': 'Sugar', 'quantity': '1', 'unit': 'cup'}),
            content_type='application/json')

        # Add first time
        response1 = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        data1 = json.loads(response1.data)
        assert data1['added_count'] == 2
        assert data1['skipped_count'] == 0

        # Add second time
        response2 = client.post(f'/api/recipes/{recipe_id}/add-to-shopping-list')
        data2 = json.loads(response2.data)
        assert data2['added_count'] == 0
        assert data2['skipped_count'] == 2

        # Verify still only 2 items
        items = json.loads(client.get(f'/api/lists/{list_id}/items').data)
        assert len(items) == 2
