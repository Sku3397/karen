
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_pubsub_topic" "task_assignments" {
  name = "handyman-task-assignments"
}

resource "google_pubsub_topic" "task_results" {
  name = "handyman-task-results"
}

resource "google_firestore_database" "default" {
  name     = "(default)"
  location_id = var.region
  type     = "NATIVE"
}

resource "google_firestore_backup_schedule" "main_backup" {
  database = google_firestore_database.default.name
  retention = "30d"
  schedule = "0 2 * * *" # Daily at 2 AM
}

resource "google_project_service" "functions" {
  service = "cloudfunctions.googleapis.com"
}

resource "google_project_service" "monitoring" {
  service = "monitoring.googleapis.com"
}

resource "google_project_service" "logging" {
  service = "logging.googleapis.com"
}

resource "google_project_service" "pubsub" {
  service = "pubsub.googleapis.com"
}

resource "google_project_service" "firestore" {
  service = "firestore.googleapis.com"
}

resource "google_cloudfunctions2_function" "handyman_function" {
  name        = "handyman-function"
  location    = var.region
  build_config {
    runtime     = "python311"
    entry_point = "main"
    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_zip
      }
    }
  }
  service_config {
    min_instance_count = 0
    max_instance_count = 10
    available_memory   = "512M"
    timeout_seconds    = 60
    environment_variables = {
      "ENV" = "production"
    }
  }
  event_trigger {
    event_type = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = google_pubsub_topic.task_assignments.id
    retry_policy = "RETRY_POLICY_RETRY"
  }
  depends_on = [
    google_project_service.functions,
    google_project_service.pubsub
  ]
}

resource "google_logging_project_sink" "cloudfunctions_log_sink" {
  name        = "cloudfunctions-logs-sink"
  destination = "logging.googleapis.com/projects/${var.project_id}/logs/cloudaudit.googleapis.com%2Factivity"
  filter      = "resource.type=cloud_function"
}

resource "google_monitoring_dashboard" "main_dashboard" {
  dashboard_json = file("${path.module}/dashboard.json")
}
