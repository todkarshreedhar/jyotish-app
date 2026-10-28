locals {
  api_env = {
    ENVIRONMENT = var.environment
    WEB_URL     = var.web_url
    REDIS_URL   = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
    APP_VERSION = var.api_image
  }
  api_secrets = merge({ for k, s in google_secret_manager_secret.app : k => s.secret_id }, { DATABASE_URL = google_secret_manager_secret.database_url.secret_id })
}

# API: migrations run as the "migrate" Cloud Run job (below) before each deploy.
resource "google_cloud_run_v2_service" "api" {
  name     = "${local.name}-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = local.prod ? 1 : 0
      max_instance_count = 10
    }
    vpc_access {
      connector = google_vpc_access_connector.run.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    containers {
      image   = var.api_image
      command = ["uv", "run", "--no-sync", "uvicorn", "jyotish_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
      ports {
        container_port = 8000
      }
      resources {
        limits = { cpu = "2", memory = "1Gi" }
      }
      dynamic "env" {
        for_each = local.api_env
        content {
          name  = env.key
          value = env.value
        }
      }
      dynamic "env" {
        for_each = local.api_secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
      startup_probe {
        http_get {
          path = "/health"
        }
      }
    }
  }
}

# Worker: PDF reports, daily alerts and clean-up. CPU stays on for Celery.
resource "google_cloud_run_v2_service" "worker" {
  name     = "${local.name}-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.api.email
    scaling {
      min_instance_count = 1
      max_instance_count = 1 # one beat scheduler
    }
    vpc_access {
      connector = google_vpc_access_connector.run.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
    containers {
      image   = var.api_image
      command = ["sh", "-c", "python -m http.server 8080 & uv run --no-sync celery -A jyotish_api.worker worker --beat --loglevel=info"]
      ports {
        container_port = 8080
      }
      resources {
        cpu_idle = false
        limits   = { cpu = "1", memory = "1Gi" }
      }
      dynamic "env" {
        for_each = local.api_env
        content {
          name  = env.key
          value = env.value
        }
      }
      dynamic "env" {
        for_each = local.api_secrets
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "web" {
  name     = "${local.name}-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      min_instance_count = local.prod ? 1 : 0
      max_instance_count = 10
    }
    containers {
      image = var.web_image
      ports {
        container_port = 3000
      }
      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = { api = google_cloud_run_v2_service.api.name, web = google_cloud_run_v2_service.web.name }
  name     = each.value
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Database migrations: run before each deploy with
#   gcloud run jobs execute jyotish-<env>-migrate --region asia-south1 --wait
resource "google_cloud_run_v2_job" "migrate" {
  name     = "${local.name}-migrate"
  location = var.region

  template {
    template {
      service_account = google_service_account.api.email
      max_retries     = 0
      vpc_access {
        connector = google_vpc_access_connector.run.id
        egress    = "PRIVATE_RANGES_ONLY"
      }
      containers {
        image   = var.api_image
        command = ["uv", "run", "--no-sync", "alembic", "upgrade", "head"]
        dynamic "env" {
          for_each = local.api_env
          content {
            name  = env.key
            value = env.value
          }
        }
        dynamic "env" {
          for_each = local.api_secrets
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
}
