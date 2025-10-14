#!/bin/bash

# Cron job script to check for new Docker images and deploy
# This script runs every 2 minutes and checks for new images

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/k8s-cron.log"
LAST_IMAGE_FILE="/tmp/last-deployed-image.txt"
DOCKER_USERNAME=${DOCKER_USERNAME:-"your-docker-username"}
IMAGE_NAME="$DOCKER_USERNAME/distributedproject"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🔍 Cron job started - checking for new images"

# Check if we have a record of the last deployed image
if [ -f "$LAST_IMAGE_FILE" ]; then
    LAST_IMAGE=$(cat "$LAST_IMAGE_FILE")
    log "📋 Last deployed image: $LAST_IMAGE"
else
    log "📋 No previous deployment record found"
    LAST_IMAGE=""
fi

# Check if there's a new image available using Docker Hub API
log "🔍 Checking for new image: $IMAGE_NAME:latest"

# Get the latest image digest from Docker Hub API
LATEST_DIGEST=$(curl -s "https://hub.docker.com/v2/repositories/$IMAGE_NAME/tags/latest/" | jq -r '.digest' 2>/dev/null || echo "")

if [ -n "$LATEST_DIGEST" ] && [ "$LATEST_DIGEST" != "null" ]; then
    log "📦 Latest image digest from Docker Hub: $LATEST_DIGEST"
    
    # Check if this is a new image
    if [ "$LAST_IMAGE" != "$LATEST_DIGEST" ]; then
        log "🆕 New image detected! Pulling and deploying..."
        
        # Pull the latest image
        if docker pull "$IMAGE_NAME:latest"; then
            log "✅ Successfully pulled latest image"
            
            # Deploy to test environment
            if "$SCRIPT_DIR/local-deploy.sh" test latest; then
                log "✅ Test environment deployment successful"
                
                # Update the last deployed image record
                echo "$LATEST_DIGEST" > "$LAST_IMAGE_FILE"
                log "💾 Updated deployment record"
            else
                log "❌ Test environment deployment failed"
            fi
        else
            log "❌ Failed to pull latest image"
        fi
    else
        log "✅ No new image - skipping deployment"
    fi
else
    log "❌ Failed to get image digest from Docker Hub API"
    log "🔍 Trying direct pull as fallback..."
    
    # Fallback: try to pull and check locally
    if docker pull "$IMAGE_NAME:latest" &> /dev/null; then
        NEW_IMAGE_DIGEST=$(docker inspect "$IMAGE_NAME:latest" --format='{{.Id}}')
        log "📦 Local image digest: $NEW_IMAGE_DIGEST"
        
        if [ "$LAST_IMAGE" != "$NEW_IMAGE_DIGEST" ]; then
            log "🆕 New image detected via fallback! Deploying..."
            
            if "$SCRIPT_DIR/local-deploy.sh" test latest; then
                log "✅ Test environment deployment successful"
                echo "$NEW_IMAGE_DIGEST" > "$LAST_IMAGE_FILE"
                log "💾 Updated deployment record"
            else
                log "❌ Test environment deployment failed"
            fi
        else
            log "✅ No new image - skipping deployment"
        fi
    else
        log "❌ Failed to pull image or no new image available"
    fi
fi

log "🏁 Cron job completed"
