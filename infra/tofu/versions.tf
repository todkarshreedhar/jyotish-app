terraform {
  required_version = ">= 1.8"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # State lives in a Cloud Storage bucket you create once by hand:
  #   gcloud storage buckets create gs://<project>-tofu-state --location=asia-south1 --uniform-bucket-level-access
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}
