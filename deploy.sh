#!/bin/bash

# Deployment script for Kubernetes environments
# Usage: ./deploy.sh [dev|test|prod] [image-tag]

set -e

ENVIRONMENT=${1:-test}
IMAGE_TAG=${2:-latest}
NAMESPACE=$ENVIRONMENT
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-docker-username"}
IMAGE_NAME="$DOCKER_USERNAME/distributedproject"

echo "Deploying to $ENVIRONMENT environment with image tag: $IMAGE_TAG"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Update the deployment with the new image
if [ "$ENVIRONMENT" = "dev" ]; then
    kubectl set image deployment/notes-app notes-app=$IMAGE_NAME:$IMAGE_TAG -n $NAMESPACE
    kubectl apply -f k8s/deployment-dev.yaml
    kubectl apply -f k8s/service.yaml
elif [ "$ENVIRONMENT" = "test" ]; then
    kubectl set image deployment/notes-app notes-app=$IMAGE_NAME:$IMAGE_TAG -n $NAMESPACE
    kubectl apply -f k8s/deployment-test.yaml
    kubectl apply -f k8s/service.yaml
elif [ "$ENVIRONMENT" = "prod" ]; then
    kubectl set image deployment/notes-app notes-app=$IMAGE_NAME:$IMAGE_TAG -n $NAMESPACE
    kubectl apply -f k8s/deployment-prod.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
else
    echo "Invalid environment. Use 'dev', 'test', or 'prod'"
    exit 1
fi

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
kubectl rollout status deployment/notes-app -n $NAMESPACE --timeout=300s

# Show deployment status
echo "Deployment completed. Status:"
kubectl get pods -n $NAMESPACE -l app=notes-app
kubectl get services -n $NAMESPACE

echo "Deployment to $ENVIRONMENT environment completed successfully!"
