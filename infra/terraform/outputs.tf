output "cloud_run_url" {
  value = google_cloud_run_service.main.status[0].url
  description = "URL of the deployed Cloud Run service."
}

output "cloud_function_url" {
  value = google_cloudfunctions_function.main.https_trigger_url
  description = "URL of the deployed Cloud Function."
}

output "pubsub_topic" {
  value = google_pubsub_topic.main.name
  description = "Pub/Sub topic name."
}

output "firestore_database" {
  value = google_firestore_database.default.name
  description = "Firestore database name."
}
