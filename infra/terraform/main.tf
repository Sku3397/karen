terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.50.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_services" {
  for_each = toset([
    "firestore.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "pubsub.googleapis.com",
    "cloudscheduler.googleapis.com",
    "compute.googleapis.com"
  ])
  service = each.value
}

# Firestore
resource "google_firestore_database" "default" {
  name        = "(default)"
  project     = var.project_id
  location_id = var.region
  type        = "NATIVE"
}

# VPC Network
resource "google_compute_network" "vpc_network" {
  name                    = var.vpc_network_name
  auto_create_subnetworks = true
}

# Cloud Run Service
resource "google_cloud_run_service" "main" {
  name     = var.cloud_run_service_name
  location = var.region
  template {
    spec {
      containers {
        image = var.cloud_run_container_image
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Grant invoker role to all users (lock down for production)
resource "google_cloud_run_service_iam_member" "invoker" {
  service    = google_cloud_run_service.main.name
  location   = var.region
  role       = "roles/run.invoker"
  member     = "allUsers"
}

# Cloud Functions
resource "google_cloudfunctions_function" "main" {
  name        = var.cloud_function_name
  description = "Main function for event handling."
  runtime     = var.cloud_function_runtime
  entry_point = var.cloud_function_entry_point
  source_archive_bucket = var.cloud_function_source_bucket
  source_archive_object = var.cloud_function_source_object
  trigger_http = true
  available_memory_mb = 256
  region = var.region
  vpc_connector = google_vpc_access_connector.connector.name
  environment_variables = var.cloud_function_env
}

# VPC Connector for Cloud Functions
resource "google_vpc_access_connector" "connector" {
  name          = "serverless-connector"
  region        = var.region
  network       = google_compute_network.vpc_network.name
  ip_cidr_range = "10.8.0.0/28"
}

# Pub/Sub Topic
resource "google_pubsub_topic" "main" {
  name = var.pubsub_topic_name
}

# Cloud Scheduler Job (publishes to Pub/Sub)
resource "google_cloud_scheduler_job" "main" {
  name             = var.scheduler_job_name
  description      = "Trigger scheduled tasks via Pub/Sub."
  schedule         = var.scheduler_cron
  time_zone        = var.scheduler_tz
  pubsub_target {
    topic_name = google_pubsub_topic.main.id
    data       = base64encode("{\"action\":\"scheduled_task\"}")
  }
}
