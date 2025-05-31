# Deploy to Cloud Run

# Deploy service to us-central1
 gcloud run deploy ai-handyman --image gcr.io/project-id/ai-handyman:latest --region us-central1 --allow-unauthenticated

# Deploy service to europe-west1
 gcloud run deploy ai-handyman --image gcr.io/project-id/ai-handyman:latest --region europe-west1 --allow-unauthenticated

# Setup Global Load Balancer
## Assuming the backend services and URL map are already defined in the Terraform config

# Update CDN configurations
## Enable CDN on the Backend Service
 gcloud compute backend-services update ai-handyman --enable-cdn --global

# Define auto-scaling policies
 gcloud run services update ai-handyman --min-instances=1 --max-instances=10 --cpu-threshold=75 --memory-threshold=80 --region=us-central1
 gcloud run services update ai-handyman --min-instances=1 --max-instances=10 --cpu-threshold=75 --memory-threshold=80 --region=europe-west1