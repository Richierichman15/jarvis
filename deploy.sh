#!/bin/bash
set -e

# Default values
PLATFORM=""
TAG="latest"
IMAGE_NAME="jarvis-app"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build the Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME:$TAG .

case $PLATFORM in
    "railway")
        echo "Pushing to Railway..."
        docker tag $IMAGE_NAME:$TAG railway.app/$IMAGE_NAME:$TAG
        docker push railway.app/$IMAGE_NAME:$TAG
        ;;
    "render")
        echo "Pushing to Render..."
        # Render specific deployment commands
        echo "Please configure Render deployment in your Render dashboard"
        ;;
    "fly")
        echo "Pushing to Fly.io..."
        flyctl deploy --image $IMAGE_NAME:$TAG
        ;;
    *)
        echo "No platform specified. Image built locally as $IMAGE_NAME:$TAG"
        echo "Available platforms: railway, render, fly"
        ;;
esac

echo "Deployment completed!"
