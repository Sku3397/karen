
output "pubsub_topic_task_assignments" {
  value = google_pubsub_topic.task_assignments.name
}

output "pubsub_topic_task_results" {
  value = google_pubsub_topic.task_results.name
}

output "firestore_database" {
  value = google_firestore_database.default.name
}

output "cloud_function_name" {
  value = google_cloudfunctions2_function.handyman_function.name
}
