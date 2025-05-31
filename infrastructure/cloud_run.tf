resource "google_cloud_run_service" "handyman" {
  name     = "ai-handyman-service"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/project-id/handyman:latest"
        ports {
          container_port = 8080
        }
      }
      container_concurrency = 80
      service_account_name  = google_service_account.handyman_sa.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  meta {
    annotations = {
      "run.googleapis.com/vpc-access-connector" = "projects/project-id/locations/us-central1/connectors/vpc-connector"
    }
  }
}