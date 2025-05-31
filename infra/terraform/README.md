# GCP Infrastructure for AI Handyman Secretary Assistant

## Overview
This Terraform configuration provisions the core GCP infrastructure:
- Firestore (Native mode, regional)
- Cloud Run (containerized service)
- Cloud Functions (event-driven, HTTP-triggered)
- Pub/Sub (messaging)
- Cloud Scheduler (cron jobs)
- VPC networking (for secure serverless connectivity)

## Prerequisites
- [Terraform](https://www.terraform.io/downloads.html) >= 1.3
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- GCP project with billing enabled

## Usage
1. Clone the repo and cd into `infra/terraform`
2. Create a `terraform.tfvars` file with your specific values:

```
project_id                  = "your-gcp-project-id"
region                      = "us-central1"
cloud_run_container_image   = "gcr.io/your-project/your-image:tag"
cloud_function_source_bucket = "your-bucket"
cloud_function_source_object = "your-function.zip"
cloud_function_env = {
  VAR1 = "value1"
  VAR2 = "value2"
}
```

3. Initialize Terraform:
   ```
   terraform init
   ```
4. Plan and review changes:
   ```
   terraform plan
   ```
5. Apply to create resources:
   ```
   terraform apply
   ```

## Notes
- IAM roles are set for public invoker access on Cloud Run for demo; restrict for production.
- Cloud Function is deployed from a GCS bucket ZIP; update source as needed.
- VPC is auto-created with subnetworks; adjust for advanced network requirements.
