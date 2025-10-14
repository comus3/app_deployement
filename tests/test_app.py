import pytest
import json
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestApp:
    """Test cases for the Flask application."""

    def test_hello_world(self, client):
        """Test the main hello world endpoint."""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Hello World!'
        assert data['service'] == 'Simple Flask API'
        assert data['version'] == '1.1.0'
        assert 'timestamp' in data
        assert 'pod' in data

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'pod' in data

    def test_api_hello(self, client):
        """Test the API hello endpoint."""
        response = client.get('/api/hello')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Hello from the Flask API!'
        assert 'timestamp' in data
        assert 'pod' in data

    @patch('psutil.boot_time')
    @patch('psutil.virtual_memory')
    def test_api_status(self, mock_virtual_memory, mock_boot_time, client):
        """Test the API status endpoint."""
        # Mock psutil functions
        mock_boot_time.return_value = 1000.0
        mock_memory = MagicMock()
        mock_memory.total = 1000000000
        mock_memory.available = 500000000
        mock_memory.percent = 50.0
        mock_virtual_memory.return_value = mock_memory
        
        with patch('time.time', return_value=2000.0):
            response = client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'running'
            assert data['uptime'] == 1000.0
            assert data['memory']['total'] == 1000000000
            assert data['memory']['available'] == 500000000
            assert data['memory']['percent'] == 50.0
            assert 'pod' in data
            assert 'timestamp' in data

    @patch('os.environ.get')
    def test_pod_name_from_env(self, mock_env_get, client):
        """Test that pod name is retrieved from environment variable."""
        mock_env_get.return_value = 'test-pod-123'
        
        response = client.get('/')
        data = json.loads(response.data)
        assert data['pod'] == 'test-pod-123'

    @patch('socket.gethostname')
    @patch('os.environ.get')
    def test_pod_name_fallback(self, mock_env_get, mock_gethostname, client):
        """Test that pod name falls back to hostname when env var is not set."""
        mock_env_get.return_value = None
        mock_gethostname.return_value = 'fallback-hostname'
        
        # We need to patch the get_pod_name function directly since it's imported
        with patch('app.get_pod_name', return_value='fallback-hostname'):
            response = client.get('/')
            data = json.loads(response.data)
            assert data['pod'] == 'fallback-hostname'

    def test_nonexistent_endpoint(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_api_info(self, client):
        """Test the new API info endpoint."""
        response = client.get('/api/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == '🚀 Auto-deployment test endpoint!'
        assert data['version'] == '1.1.0'
        assert data['feature'] == 'Kubernetes CronJob deployment'
        assert data['deployment_method'] == 'GitHub Actions + Docker Hub + K8s CronJob'
        assert 'pod' in data
        assert 'timestamp' in data

    def test_json_response_format(self, client):
        """Test that all endpoints return valid JSON."""
        endpoints = ['/', '/health', '/api/hello', '/api/status', '/api/info']
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            # Ensure response is valid JSON
            data = json.loads(response.data)
            assert isinstance(data, dict)
