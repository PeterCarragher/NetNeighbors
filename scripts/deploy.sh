#!/bin/bash
# Deploy NetNeighbors to Google Cloud Run
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. Project configured: gcloud config set project YOUR_PROJECT
#   3. APIs enabled: Cloud Build, Cloud Run, Artifact Registry
#   4. Webgraph data uploaded to GCS
#
# Usage:
#   ./scripts/deploy.sh

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-netneighbors}"
WEBGRAPH_BUCKET="${WEBGRAPH_BUCKET:-}"
WEBGRAPH_VERSION="${WEBGRAPH_VERSION:-cc-main-2024-feb-apr-may}"

echo "============================================================"
echo "       NetNeighbors Cloud Run Deployment"
echo "============================================================"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo ""

if [ -z "$PROJECT_ID" ]; then
    echo "Error: No project configured"
    echo "Run: gcloud config set project YOUR_PROJECT"
    exit 1
fi

# Check if webgraph bucket is set
if [ -z "$WEBGRAPH_BUCKET" ]; then
    echo "Warning: WEBGRAPH_BUCKET not set"
    echo "You'll need to configure GCS volume mount manually"
    echo ""
fi

# Enable required APIs
echo "1. Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com --quiet

# Build and push with Cloud Build
echo ""
echo "2. Building and deploying..."
gcloud builds submit --config cloudbuild.yaml

echo ""
echo "============================================================"
echo "                  Deployment Complete!"
echo "============================================================"
echo ""
echo "View your app:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
