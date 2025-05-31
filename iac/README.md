# GCP Infrastructure as Code (Terraform)

## Resources Provisioned
- Pub/Sub Topic (`agent-events`)
- Firestore (Native mode)
- Cloud Function (Pub/Sub-triggered)
- Required APIs enabled

## Usage
1. Set required variables in a `terraform.tfvars` file:

```
project_id        = "your-gcp-project-id"
region            = "us-central1"
functions_bucket  = "your-gcs-bucket"
functions_object  = "your-function-archive.zip"
```

2. Initialize and apply:
```
terraform init
terraform apply
```
