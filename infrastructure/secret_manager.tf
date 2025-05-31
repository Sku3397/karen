resource "google_secret_manager_secret" "api_keys" {
  secret_id = "api-keys"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "api_keys_version" {
  secret      = google_secret_manager_secret.api_keys.id
  secret_data = "Sensitive data here"
}