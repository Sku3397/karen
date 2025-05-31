# Terraform configuration for GCP AI Handyman Secretary Assistant
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "project" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])
  service = each.value
  project = var.project_id
}

resource "google_pubsub_topic" "agent_topic" {
  name = "agent-events"
}

resource "google_firestore_database" "default" {
  name     = "(default)"
  location_id = var.region
  project  = var.project_id
  type     = "NATIVE"
}

resource "google_cloudfunctions_function" "agent_function" {
  name        = "agent-handler"
  runtime     = "python310"
  available_memory_mb   = 512
  source_archive_bucket = var.functions_bucket
  source_archive_object = var.functions_object
  entry_point           = "main"
  trigger_http          = false
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.agent_topic.id
  }
  environment_variables = {
    "FIRESTORE_PROJECT" = var.project_id
    "PUBSUB_TOPIC"      = google_pubsub_topic.agent_topic.name
  }
}
