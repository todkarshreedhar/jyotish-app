variable "project_id" {
  description = "Google Cloud project ID."
  type        = string
}

variable "region" {
  description = "Region for everything. Mumbai keeps data in India (DPDP Act)."
  type        = string
  default     = "asia-south1"
}

variable "environment" {
  description = "staging or production."
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "web_url" {
  description = "Public URL of the web app, for example https://jyotish.example.org"
  type        = string
}

variable "api_image" {
  description = "Container image for the API and worker (built from apps/api/Dockerfile)."
  type        = string
}

variable "web_image" {
  description = "Container image for the web app."
  type        = string
}

variable "alert_email" {
  description = "Who gets an email when the site is down (the on-call person)."
  type        = string
}

variable "db_tier" {
  description = "Cloud SQL machine type."
  type        = string
  default     = "db-custom-1-3840"
}
