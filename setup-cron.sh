#!/bin/bash

# Setup script for the Kubernetes deployment cron job
# This script sets up a cron job to check for new Docker images every 2 minutes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/cron-deploy.sh"

echo "🔧 Setting up Kubernetes deployment cron job..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    echo "   Install instructions: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ docker not found. Please install Docker first."
    echo "   Install instructions: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if we can access Docker Hub
echo "🔍 Testing access to Docker Hub..."
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-docker-username"}
if ! docker pull "$DOCKER_USERNAME/distributedproject:latest" &> /dev/null; then
    echo "❌ Cannot access $DOCKER_USERNAME/distributedproject:latest"
    echo "   Please ensure you're logged in to Docker Hub:"
    echo "   docker login"
    echo "   Or set DOCKER_USERNAME environment variable:"
    echo "   export DOCKER_USERNAME=your-docker-username"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create the cron job
echo "📅 Setting up cron job to run every 2 minutes..."

# Remove any existing cron job for this script
(crontab -l 2>/dev/null | grep -v "$CRON_SCRIPT" || true) | crontab -

# Add the new cron job
(crontab -l 2>/dev/null; echo "*/2 * * * * $CRON_SCRIPT >> /tmp/k8s-cron.log 2>&1") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 Cron job details:"
echo "   - Script: $CRON_SCRIPT"
echo "   - Schedule: Every 2 minutes"
echo "   - Log file: /tmp/k8s-cron.log"
echo ""
echo "🔍 To view the cron job:"
echo "   crontab -l"
echo ""
echo "📊 To monitor the deployment:"
echo "   tail -f /tmp/k8s-cron.log"
echo ""
echo "🛑 To remove the cron job:"
echo "   crontab -e  # Then delete the line with $CRON_SCRIPT"
echo ""
echo "🎉 Setup complete! The cron job will now check for new images every 2 minutes."
