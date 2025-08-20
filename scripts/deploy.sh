#!/usr/bin/env bash
set -euo pipefail

# Load environment variables from .env if present
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

SERVICE_NAME=${SERVICE_NAME:-slack-gemini-bot}
REGION=${REGION:-us-central1}
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [[ -z "${SLACK_BOT_TOKEN:-}" || -z "${SLACK_SIGNING_SECRET:-}" ]]; then
  echo "SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET environment variables must be set" >&2
  exit 1
fi

gcloud builds submit --tag "$IMAGE"

gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN},SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET},GOOGLE_PROJECT=${PROJECT_ID},GOOGLE_LOCATION=${REGION}"
