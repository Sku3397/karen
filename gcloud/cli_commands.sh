#!/bin/bash
# Deploy to Google Cloud Run

gcloud run deploy ai-handyman-service --image gcr.io/[PROJECT-ID]/ai-handyman:latest --region us-central1
# Repeat deployment for additional regions

gcloud compute forwarding-rules create ai-handyman-load-balancer --global --target-http-proxy TARGET_PROXY_NAME --ports 80

# Setup Cloud Monitoring
#gcloud beta monitoring dashboards create --config-from-file monitoring-dashboard.json
