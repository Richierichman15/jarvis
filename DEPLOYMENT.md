# Deployment Guide

This guide explains how to deploy Jarvis to various cloud platforms using Docker.

## Prerequisites

- Docker installed locally
- Account on your chosen cloud platform (Railway, Render, Fly.io, etc.)
- Docker Hub account (optional, for pushing images)

## Building the Docker Image

```bash
# Build the image
docker build -t jarvis-app .

# Run locally for testing
docker run -p 5000:5000 -e PORT=5000 jarvis-app
```

## Deployment Options

### Option 1: Using the deployment script

1. Make the script executable:
   ```bash
   chmod +x deploy.sh
   ```

2. Deploy to your chosen platform:
   ```bash
   # For Railway
   ./deploy.sh --platform railway --tag v1.0.0

   # For Fly.io
   ./deploy.sh --platform fly --tag v1.0.0
   ```

### Option 2: Manual Deployment

#### Railway
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Link your project: `railway link`
4. Deploy: `railway up`

#### Render
1. Create a new Web Service
2. Connect your GitHub repository
3. Set the following environment variables:
   - `PORT`: 10000
   - Other required environment variables
4. Deploy

#### Fly.io
1. Install Fly CLI: `brew install flyctl`
2. Login: `flyctl auth login`
3. Launch: `flyctl launch`
4. Deploy: `flyctl deploy`

## Environment Variables

Make sure to set these environment variables in your deployment:

- `PORT`: The port the app will run on (default: 5000)
- `OPENAI_API_KEY`: Your OpenAI API key (if using OpenAI models)
- Any other required API keys or configuration

## Health Check

The application includes a health check endpoint at `/health` that can be used by your deployment platform to verify the application is running.

## Troubleshooting

- If the app fails to start, check the logs:
  ```bash
  docker logs <container_id>
  ```
- Make sure all required environment variables are set
- Check that the port is correctly mapped and not blocked by a firewall
