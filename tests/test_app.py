import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from bson import ObjectId
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_mongo():
    """Mock MongoDB connection."""
    with patch('app.MongoClient') as mock_client:
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value = mock_db
        yield mock_collection

@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch('app.redis.Redis') as mock_redis_class:
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        yield mock_redis_instance

class TestApp:
    """Test cases for the Flask application."""

    def test_index(self, client):
        """Test the main index endpoint."""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Community Notes API'
        assert data['service'] == 'Simple Notes Sharing Service'
        assert 'endpoints' in data

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'pod' in data
        assert 'services' in data

    def test_create_note_success(self, client, mock_mongo, mock_redis):
        """Test creating a note."""
        # Mock MongoDB insert
        mock_mongo.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        response = client.post('/api/notes', 
                             json={'title': 'Test Note', 'content': 'This is test content'},
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'note_id' in data
        assert data['title'] == 'Test Note'
        assert data['content'] == 'This is test content'

    def test_create_note_missing_title(self, client):
        """Test creating note without title."""
        response = client.post('/api/notes', 
                             json={'content': 'Some content'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_note_missing_content(self, client):
        """Test creating note without content."""
        response = client.post('/api/notes', 
                             json={'title': 'Test'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_all_notes(self, client, mock_mongo, mock_redis):
        """Test getting all notes."""
        mock_mongo.find.return_value.sort.return_value.limit.return_value = [
            {
                '_id': ObjectId(),
                'title': 'Note 1',
                'content': 'Content 1',
                'created_at': '2024-01-01'
            }
        ]
        
        response = client.get('/api/notes')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'notes' in data
        assert 'count' in data

    def test_get_note_by_id(self, client, mock_mongo):
        """Test getting a specific note by ID."""
        note_id = ObjectId()
        mock_mongo.find_one.return_value = {
            '_id': note_id,
            'title': 'Test Note',
            'content': 'Test content',
            'created_at': '2024-01-01'
        }
        
        response = client.get(f'/api/notes/{note_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['note_id'] == str(note_id)
        assert data['title'] == 'Test Note'

    def test_get_note_not_found(self, client, mock_mongo):
        """Test getting non-existent note."""
        mock_mongo.find_one.return_value = None
        
        response = client.get(f'/api/notes/{ObjectId()}')
        assert response.status_code == 404

    def test_stats(self, client, mock_mongo):
        """Test the stats endpoint."""
        mock_mongo.count_documents.return_value = 10
        
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_notes' in data

    def test_migration_status(self, client, mock_mongo):
        """Test migration status endpoint."""
        mock_mongo.count_documents.side_effect = [20, 15]  # total, migrated
        
        response = client.get('/api/migration_status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['total_notes'] == 20
        assert data['migrated_notes'] == 15
        assert data['pending'] == 5

    def test_run_migration(self, client, mock_mongo):
        """Test running a migration."""
        mock_result = MagicMock()
        mock_result.modified_count = 5
        mock_mongo.update_many.return_value = mock_result
        
        response = client.post('/run_migration')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data

    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    @patch('os.environ.get')
    def test_pod_name_from_env(self, mock_env_get, client):
        """Test that pod name is retrieved from environment variable."""
        mock_env_get.return_value = 'test-pod-123'
        
        response = client.get('/')
        data = json.loads(response.data)
        assert data['pod'] == 'test-pod-123'
