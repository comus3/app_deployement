# Flask API - Kubernetes Deployment Pipeline

A simple Flask API with CI/CD pipeline for Kubernetes deployment.

## Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── tests/                # Unit tests
│   ├── __init__.py
│   └── test_app.py
├── k8s/                  # Kubernetes manifests
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── deployment-test.yaml
│   ├── deployment-prod.yaml
│   ├── service.yaml
│   └── ingress.yaml
└── .github/workflows/    # CI/CD pipeline
    └── ci-cd.yml
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow that:

1. **Runs unit tests** on every push and pull request
2. **Builds Docker image** and pushes to GitHub Container Registry
3. **Deploys to test environment** when pushing to `develop` branch
4. **Deploys to production** when pushing to `main` branch

### Workflow Triggers

- **Push to `main`**: Runs tests, builds image, deploys to production
- **Push to `develop`**: Runs tests, builds image, deploys to test
- **Pull requests**: Runs tests only

## Local Development

### Prerequisites

- Python 3.11+
- Docker
- Kubernetes cluster (Docker Desktop, Minikube, etc.)

### Setup

1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Run tests:
   ```bash
   pytest tests/ -v
   ```

### Docker

Build and run the container:

```bash
# Build image
docker build -t flask-api .

# Run container
docker run -p 5000:5000 flask-api
```

### Kubernetes Deployment

1. Create namespaces:
   ```bash
   kubectl apply -f k8s/namespace.yaml
   ```

2. Deploy to test environment:
   ```bash
   kubectl apply -f k8s/deployment-test.yaml
   kubectl apply -f k8s/service.yaml
   ```

3. Deploy to production:
   ```bash
   kubectl apply -f k8s/deployment-prod.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

## API Endpoints

- `GET /` - Hello world message
- `GET /health` - Health check
- `GET /api/hello` - API hello message
- `GET /api/status` - System status and metrics

## Environment Variables

- `PORT` - Application port (default: 5000)
- `FLASK_ENV` - Flask environment (production/development)
- `HOSTNAME` - Pod hostname for identification

## Monitoring

The application includes:
- Health check endpoint (`/health`)
- System metrics endpoint (`/api/status`)
- Kubernetes health probes (liveness and readiness)

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Deployment Strategy

- **Test Environment**: 2 replicas, lower resource limits
- **Production Environment**: 3 replicas, higher resource limits
- **Rolling Updates**: Zero-downtime deployments
- **Health Checks**: Automatic restart of unhealthy pods
