variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region (e.g. us-central1)"
  type        = string
  default     = "us-central1"
}

variable "vpc_network_name" {
  description = "VPC network name"
  type        = string
  default     = "handyman-vpc"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "handyman-service"
}

variable "cloud_run_container_image" {
  description = "Cloud Run container image URI"
  type        = string
}

variable "cloud_function_name" {
  description = "Cloud Function name"
  type        = string
  default     = "handyman-function"
}

variable "cloud_function_runtime" {
  description = "Cloud Function runtime (e.g. python310)"
  type        = string
  default     = "python310"
}

variable "cloud_function_entry_point" {
  description = "Cloud Function entry point"
  type        = string
  default     = "main"
}

variable "cloud_function_source_bucket" {
  description = "Source bucket for Cloud Function zip"
  type        = string
}

variable "cloud_function_source_object" {
  description = "Source object (zip) in bucket"
  type        = string
}

variable "cloud_function_env" {
  description = "Environment variables for Cloud Function"
  type        = map(string)
  default     = {}
}

variable "pubsub_topic_name" {
  description = "Pub/Sub topic name"
  type        = string
  default     = "handyman-topic"
}

variable "scheduler_job_name" {
  description = "Cloud Scheduler job name"
  type        = string
  default     = "handyman-scheduler"
}

variable "scheduler_cron" {
  description = "Cron schedule expression for Cloud Scheduler"
  type        = string
  default     = "* * * * *"
}

variable "scheduler_tz" {
  description = "Timezone for Cloud Scheduler job"
  type        = string
  default     = "Etc/UTC"
}
