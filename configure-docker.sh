#!/bin/bash

# Configuration script for Docker Hub deployment
# This script helps set up the Docker username for local deployment

set -e

echo "🐳 Docker Hub Configuration Setup"
echo "=================================="
echo ""

# Check if DOCKER_USERNAME is already set
if [ -n "$DOCKER_USERNAME" ]; then
    echo "✅ DOCKER_USERNAME is already set: $DOCKER_USERNAME"
else
    echo "❌ DOCKER_USERNAME is not set"
    echo ""
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    
    if [ -z "$DOCKER_USERNAME" ]; then
        echo "❌ No username provided. Exiting."
        exit 1
    fi
fi

echo ""
echo "🔧 Setting up environment..."

# Create a .env file for local use
cat > .env << EOF
# Docker Hub Configuration
DOCKER_USERNAME=$DOCKER_USERNAME
EOF

echo "✅ Created .env file with DOCKER_USERNAME=$DOCKER_USERNAME"

# Update Kubernetes deployment files
echo "📝 Updating Kubernetes deployment files..."

# Update test deployment
sed -i "s/your-docker-username/$DOCKER_USERNAME/g" k8s/deployment-test.yaml
echo "✅ Updated k8s/deployment-test.yaml"

# Update production deployment
sed -i "s/your-docker-username/$DOCKER_USERNAME/g" k8s/deployment-prod.yaml
echo "✅ Updated k8s/deployment-prod.yaml"

echo ""
echo "🎉 Configuration complete!"
echo ""
echo "📋 Next steps:"
echo "1. Login to Docker Hub: docker login"
echo "2. Set up the cron job: ./setup-cron.sh"
echo "3. Test manual deployment: ./local-deploy.sh test latest"
echo ""
echo "🔍 To verify configuration:"
echo "   cat .env"
echo "   grep -r '$DOCKER_USERNAME' k8s/"
