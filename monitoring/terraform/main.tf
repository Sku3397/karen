# Google Cloud Monitoring - Dashboards & Alerts
provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_monitoring_dashboard" "system_health" {
  dashboard_json = <<EOF
  {
    "displayName": "System Health Overview",
    "gridLayout": {
      "columns": 2,
      "widgets": [
        {
          "title": "App Engine: Request Latency",
          "xyChart": {
            "dataSets": [
              {"timeSeriesQuery": {"timeSeriesFilter": {"filter": "metric.type=\"appengine.googleapis.com/http/server/response_latencies\""}}}
            ]
          }
        },
        {
          "title": "Firestore: Document Reads",
          "xyChart": {
            "dataSets": [
              {"timeSeriesQuery": {"timeSeriesFilter": {"filter": "metric.type=\"firestore.googleapis.com/document/read_count\""}}}
            ]
          }
        },
        {
          "title": "CPU Utilization (GKE)",
          "xyChart": {
            "dataSets": [
              {"timeSeriesQuery": {"timeSeriesFilter": {"filter": "metric.type=\"kubernetes.io/container/cpu/usage_time\""}}}
            ]
          }
        },
        {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [
              {"timeSeriesQuery": {"timeSeriesFilter": {"filter": "metric.type=\"logging.googleapis.com/user/error_count\""}}}
            ]
          }
        }
      ]
    }
  }
EOF
}

resource "google_monitoring_dashboard" "cost_dashboard" {
  dashboard_json = <<EOF
  {
    "displayName": "Cost Optimization",
    "gridLayout": {
      "columns": 1,
      "widgets": [
        {
          "title": "Estimated Billing (GCP)",
          "xyChart": {
            "dataSets": [
              {"timeSeriesQuery": {"timeSeriesFilter": {"filter": "metric.type=\"billing.googleapis.com/billing/account/estimated_charges\""}}}
            ]
          }
        }
      ]
    }
  }
EOF
}

resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Application Error Rate"
  combiner     = "OR"
  notification_channels = [var.notification_channel_id]

  conditions {
    display_name = "App Error Rate above 2%"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/error_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 2
      duration        = "300s"
      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "High Request Latency"
  combiner     = "OR"
  notification_channels = [var.notification_channel_id]

  conditions {
    display_name = "Request Latency > 1000ms"
    condition_threshold {
      filter          = "metric.type=\"appengine.googleapis.com/http/server/response_latencies\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1000
      duration        = "300s"
      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "high_cost_estimate" {
  display_name = "High Estimated Billing Cost"
  combiner     = "OR"
  notification_channels = [var.notification_channel_id]

  conditions {
    display_name = "Estimated Billing > $500"
    condition_threshold {
      filter          = "metric.type=\"billing.googleapis.com/billing/account/estimated_charges\""
      comparison      = "COMPARISON_GT"
      threshold_value = 500
      duration        = "3600s"
      trigger {
        count = 1
      }
    }
  }
}
