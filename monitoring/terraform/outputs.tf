output "system_health_dashboard_id" {
  value = google_monitoring_dashboard.system_health.id
}

output "cost_dashboard_id" {
  value = google_monitoring_dashboard.cost_dashboard.id
}
