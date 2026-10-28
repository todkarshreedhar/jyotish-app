# US-57: the on-call person gets an email within 5 minutes of downtime.

resource "google_monitoring_notification_channel" "oncall" {
  display_name = "Jyotish on-call (${var.environment})"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_uptime_check_config" "health" {
  for_each     = { web = "/", api = "/api/health" }
  display_name = "${local.name} ${each.key}"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = each.value
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(var.web_url, "https://", "")
    }
  }
}

resource "google_monitoring_alert_policy" "down" {
  for_each     = google_monitoring_uptime_check_config.health
  display_name = "${local.name} ${each.key} is down"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failing"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${each.value.uptime_check_id}\" AND resource.type=\"uptime_url\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "120s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.*"]
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.oncall.id]
  alert_strategy {
    auto_close = "1800s"
  }
}

resource "google_monitoring_alert_policy" "api_errors" {
  display_name = "${local.name} API 5xx errors"
  combiner     = "OR"
  conditions {
    display_name = "More than 5% of API requests fail"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${google_cloud_run_v2_service.api.name}\" AND metric.label.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.oncall.id]
}
