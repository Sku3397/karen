resource "google_cloud_run_service" "ai_handyman" {
  name     = "ai-handyman-service"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/project-id/ai-handyman:latest"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_compute_global_forwarding_rule" "default" {
  name       = "ai-handyman-load-balancer"
  target     = google_compute_target_http_proxy.default.id
  port_range = "80-443"
}

resource "google_compute_target_http_proxy" "default" {
  url_map = google_compute_url_map.default.id
}

resource "google_compute_url_map" "default" {
  name            = "ai-handyman-url-map"
  default_service = google_cloud_run_service.ai_handyman.status[0].url
}

resource "google_compute_backend_service" "default" {
  load_balancing_scheme = "EXTERNAL"
  protocol              = "HTTP"

  backend {
    group = google_cloud_run_service.ai_handyman.id
  }
}