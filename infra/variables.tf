
variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region to deploy resources"
  default     = "us-central1"
}

variable "source_bucket" {
  type        = string
  description = "GCS bucket containing the source code zip for Cloud Functions"
}

variable "source_zip" {
  type        = string
  description = "Zip file object name in the GCS bucket for Cloud Function source code"
}
