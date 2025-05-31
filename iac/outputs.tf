output "pubsub_topic" {
  value = google_pubsub_topic.agent_topic.name
}

output "firestore_database" {
  value = google_firestore_database.default.name
}

output "cloud_function" {
  value = google_cloudfunctions_function.agent_function.name
}
