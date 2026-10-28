output "web_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "database_instance" {
  value = google_sql_database_instance.db.connection_name
}
