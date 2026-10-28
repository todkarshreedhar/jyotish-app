locals {
  name = "jyotish-${var.environment}"
  prod = var.environment == "production"
}

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com", "sqladmin.googleapis.com", "redis.googleapis.com", "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com", "monitoring.googleapis.com", "artifactregistry.googleapis.com", "servicenetworking.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# ---------- Network (private access to the database and Redis) ----------

resource "google_compute_network" "vpc" {
  name                    = local.name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = local.name
  network       = google_compute_network.vpc.id
  region        = var.region
  ip_cidr_range = "10.10.0.0/24"
}

resource "google_compute_global_address" "private_services" {
  name          = "${local.name}-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services.name]
}

resource "google_vpc_access_connector" "run" {
  name          = "jy-${substr(var.environment, 0, 4)}"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.8.0/28"
  depends_on    = [google_project_service.apis]
}

# ---------- PostgreSQL with daily backups and point-in-time recovery ----------

resource "google_sql_database_instance" "db" {
  name                = local.name
  database_version    = "POSTGRES_17"
  region              = var.region
  deletion_protection = local.prod
  depends_on          = [google_service_networking_connection.private]

  settings {
    tier              = var.db_tier
    availability_type = local.prod ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      ssl_mode        = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "20:30" # 02:00 IST
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      location                       = var.region
      backup_retention_settings {
        retained_backups = 30
      }
    }

    maintenance_window {
      day  = 7 # Sunday
      hour = 21 # 02:30 IST
    }

    database_flags {
      name  = "cloudsql.enable_pg_trgm"
      value = "on"
    }
    insights_config {
      query_insights_enabled = true
    }
  }
}

resource "google_sql_database" "app" {
  name     = "jyotish"
  instance = google_sql_database_instance.db.name
}

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "google_sql_user" "app" {
  name     = "jyotish"
  instance = google_sql_database_instance.db.name
  password = random_password.db.result
}

# ---------- Redis (cache, rate limits, task queue) ----------

resource "google_redis_instance" "cache" {
  name               = local.name
  tier               = local.prod ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  redis_version      = "REDIS_7_2"
  depends_on         = [google_service_networking_connection.private]
}

# ---------- Secrets ----------
# Values for SECRET_KEY, DATA_ENCRYPTION_KEYS, SMTP_PASSWORD, GOOGLE_CLIENT_SECRET
# and SENTRY_DSN are added by hand (gcloud secrets versions add ...), never in code.

locals {
  secret_names = ["SECRET_KEY", "DATA_ENCRYPTION_KEYS", "SMTP_PASSWORD", "GOOGLE_CLIENT_SECRET", "SENTRY_DSN"]
}

resource "google_secret_manager_secret" "app" {
  for_each  = toset(local.secret_names)
  secret_id = "${local.name}-${lower(replace(each.value, "_", "-"))}"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${local.name}-database-url"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+psycopg://jyotish:${random_password.db.result}@${google_sql_database_instance.db.private_ip_address}:5432/jyotish?sslmode=require"
}

resource "google_service_account" "api" {
  account_id   = "${local.name}-api"
  display_name = "Jyotish API and worker"
}

resource "google_secret_manager_secret_iam_member" "api" {
  for_each  = merge({ for k, s in google_secret_manager_secret.app : k => s.id }, { DATABASE_URL = google_secret_manager_secret.database_url.id })
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}
