# Firestore Backup via GCP Scheduled Export
resource "google_storage_bucket" "firestore_backup" {
  name          = "${var.project_id}-firestore-backup"
  location      = var.gcp_region
  force_destroy = true
}

resource "google_cloud_scheduler_job" "firestore_backup_job" {
  name             = "firestore-backup-job"
  description      = "Scheduled Firestore export to GCS bucket."
  schedule         = "0 2 * * *"  # daily at 2am UTC
  time_zone        = "UTC"
  http_target {
    http_method = "POST"
    uri         = "https://firestore.googleapis.com/v1/projects/${var.project_id}/databases/(default):exportDocuments"
    oidc_token {
      service_account_email = var.scheduler_service_account
    }
    body = <<EOF
{
  "outputUriPrefix": "gs://${google_storage_bucket.firestore_backup.name}/exports"
}
EOF
    headers = {
      "Content-Type" = "application/json"
    }
  }
}
