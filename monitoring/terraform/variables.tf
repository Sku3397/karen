variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Region for resources"
  type        = string
  default     = "us-central1"
}

variable "notification_channel_id" {
  description = "Notification channel ID for alerts (email, Slack, etc.)"
  type        = string
}
