#!/bin/bash

# Deployment script for Kubernetes environments
# Usage: ./deploy.sh [test|prod] [image-tag]

set -e

ENVIRONMENT=${1:-test}
IMAGE_TAG=${2:-latest}
NAMESPACE=$ENVIRONMENT

echo "Deploying to $ENVIRONMENT environment with image tag: $IMAGE_TAG"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Update the deployment with the new image
if [ "$ENVIRONMENT" = "test" ]; then
    kubectl set image deployment/simple-api simple-api=ghcr.io/your-username/your-repo:$IMAGE_TAG -n $NAMESPACE
    kubectl apply -f k8s/deployment-test.yaml
    kubectl apply -f k8s/service.yaml
elif [ "$ENVIRONMENT" = "prod" ]; then
    kubectl set image deployment/simple-api simple-api=ghcr.io/your-username/your-repo:$IMAGE_TAG -n $NAMESPACE
    kubectl apply -f k8s/deployment-prod.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
else
    echo "Invalid environment. Use 'test' or 'prod'"
    exit 1
fi

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
kubectl rollout status deployment/simple-api -n $NAMESPACE --timeout=300s

# Show deployment status
echo "Deployment completed. Status:"
kubectl get pods -n $NAMESPACE -l app=simple-api
kubectl get services -n $NAMESPACE

echo "Deployment to $ENVIRONMENT environment completed successfully!"
