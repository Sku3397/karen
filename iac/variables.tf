variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "functions_bucket" {
  description = "Bucket for Cloud Functions source code archive"
  type        = string
}

variable "functions_object" {
  description = "Object name for Cloud Functions source code archive"
  type        = string
}
