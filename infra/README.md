# GCP Infrastructure for AI Handyman Secretary Assistant

This folder contains Terraform code to provision GCP resources:

- Pub/Sub topics for task assignment/results
- Firestore database with scheduled daily backups (30-day retention)
- Cloud Function with auto-scaling (0-10 instances), event triggered by Pub/Sub
- Cloud Monitoring and Logging enabled

## Prerequisites
- [Terraform](https://www.terraform.io/downloads.html) >= 1.3
- GCP Project (with billing enabled)
- Service account with permissions for IAM, Firestore, Pub/Sub, Cloud Functions, Monitoring, and Logging
- GCS bucket with zipped source code for Cloud Function

## Usage

1. Update `variables.tf` with your `project_id`, `region`, `source_bucket`, and `source_zip` values or provide via CLI flags/TFVARS.
2. (Optional) Edit the dashboard definition in `dashboard.json` to customize Cloud Monitoring.
3. Initialize and apply:

```sh
cd infra
terraform init
terraform apply
```

## Notes
- The Firestore backup schedule is set for daily backups with 30-day retention. Adjust as needed.
- Pub/Sub topics are created for agent event flows.
- Cloud Function auto-scales based on demand.
- Cloud Monitoring and Logging APIs are enabled and a dashboard is provisioned.
