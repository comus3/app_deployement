#!/bin/bash

# Local deployment script for Kubernetes
# This script checks for new Docker images and performs rolling updates
# Usage: ./local-deploy.sh [environment] [image-tag]

set -e

# Configuration
ENVIRONMENT=${1:-test}
IMAGE_TAG=${2:-latest}
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-docker-username"}
IMAGE_NAME="$DOCKER_USERNAME/distributedproject"
NAMESPACE=$ENVIRONMENT
LOG_FILE="/tmp/k8s-deploy.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 Checking for new image: $IMAGE_NAME:$IMAGE_TAG"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    log "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if the image exists locally
if ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" &> /dev/null; then
    log "📥 Pulling image: $IMAGE_NAME:$IMAGE_TAG"
    if ! docker pull "$IMAGE_NAME:$IMAGE_TAG"; then
        log "❌ Failed to pull image: $IMAGE_NAME:$IMAGE_TAG"
        exit 1
    fi
    log "✅ Image pulled successfully"
else
    log "✅ Image already exists locally"
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    log "📦 Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
fi

# Apply the appropriate deployment
if [ "$ENVIRONMENT" = "test" ]; then
    log "🚀 Deploying to test environment"
    kubectl apply -f k8s/deployment-test.yaml
    kubectl apply -f k8s/service.yaml
elif [ "$ENVIRONMENT" = "prod" ]; then
    log "🚀 Deploying to production environment"
    kubectl apply -f k8s/deployment-prod.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
else
    log "❌ Invalid environment. Use 'test' or 'prod'"
    exit 1
fi

# Update the image in the deployment
log "🔄 Updating deployment with new image"
kubectl set image deployment/simple-api simple-api="$IMAGE_NAME:$IMAGE_TAG" -n "$NAMESPACE"

# Wait for rollout to complete
log "⏳ Waiting for rollout to complete..."
if kubectl rollout status deployment/simple-api -n "$NAMESPACE" --timeout=300s; then
    log "✅ Rollout completed successfully"
else
    log "❌ Rollout failed or timed out"
    exit 1
fi

# Show deployment status
log "📊 Deployment status:"
kubectl get pods -n "$NAMESPACE" -l app=simple-api

# Show service status
log "🌐 Service status:"
kubectl get services -n "$NAMESPACE"

log "🎉 Deployment to $ENVIRONMENT environment completed successfully!"
