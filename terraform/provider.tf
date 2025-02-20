provider "google" {
  project = var.project_id
  region  = var.region
}

terraform {
  backend "gcs" {
    bucket = var.backend_bucket
    prefix = var.backend_prefix
  }
}
