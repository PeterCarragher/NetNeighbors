#!/bin/bash
# Deploy NetNeighbors to Google Cloud Run
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. Webgraph data uploaded to GCS bucket
#
# Usage:
#   ./scripts/deploy.sh
#
# Environment variables (all have defaults):
#   PROJECT_ID        - GCP project (default: gdelt-408523)
#   REGION            - GCP region (default: us-central1)
#   SERVICE_NAME      - Cloud Run service name (default: netneighbors)
#   WEBGRAPH_BUCKET   - GCS bucket with webgraph data (default: commoncrawl_webgraph)
#   WEBGRAPH_VERSION  - CommonCrawl version (default: cc-main-2024-feb-apr-may)

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-gdelt-408523}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-netneighbors}"
WEBGRAPH_BUCKET="${WEBGRAPH_BUCKET:-commoncrawl_webgraph}"
WEBGRAPH_VERSION="${WEBGRAPH_VERSION:-cc-main-2024-feb-apr-may}"

echo "============================================================"
echo "       NetNeighbors Cloud Run Deployment"
echo "============================================================"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Service:  $SERVICE_NAME"
echo "Bucket:   $WEBGRAPH_BUCKET"
echo "Version:  $WEBGRAPH_VERSION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID" --quiet

# Enable required APIs
echo "1. Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    --quiet

# Grant Cloud Build service account permission to deploy to Cloud Run
echo ""
echo "2. Configuring IAM permissions..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Cloud Build needs Cloud Run Admin and Service Account User roles
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --quiet 2>/dev/null || true

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet 2>/dev/null || true

# Cloud Run service account needs GCS access for volume mount
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/storage.objectViewer" \
    --quiet 2>/dev/null || true

# Build and deploy via Cloud Build
echo ""
echo "3. Building and deploying (this takes ~5 minutes)..."
gcloud builds submit \
    --config cloudbuild.yaml \
    --project "$PROJECT_ID"

echo ""
echo "============================================================"
echo "                  Deployment Complete!"
echo "============================================================"
echo ""
echo "Service URL:"
gcloud run services describe "$SERVICE_NAME" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --format 'value(status.url)'
echo ""
echo "To set up a custom domain:"
echo "  gcloud run domain-mappings create --service $SERVICE_NAME --domain YOUR_DOMAIN --region $REGION"
echo ""
