# Define the Cloud Run services dynamically based on the changed services list
module "service_check_respondent_identity" {
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.10.0"

  project_id            = var.project_id
  service_name          = "service-check-respondent-identity-tf-test-2"
  location              = var.region
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/check-respondent-identity:latest"
  service_account_email = var.service_account_email
  template_annotations  = var.template_annotations
  container_concurrency = 10
  limits                = {
    cpu    = "1000m"
    memory = "512Mi"
  }
  env_vars = [
    {
      name  = "ENV"
      value = var.environment
    }
  ]
  env_secret_vars = [
    for secret_name in [
      "GCP_PROJECT_ID",
      "TWILIO_ACCOUNT_SID",
      "TWILIO_AUTH_TOKEN",
      "TWILIO_SERVICE_SID"
    ] : {
      name      = secret_name
      value_from = [
        {
          secret_key_ref = {
            name = secret_name
            key  = "latest"
          }
        }
      ]
    }
  ]
}

resource "google_cloud_run_service_iam_member" "public_access_service_check_respondent_identity" {
  location = module.service_check_respondent_identity.location
  service  = module.service_check_respondent_identity.service_name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

module "service_processing" {
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.10.0"

  project_id            = var.project_id
  service_name          = "service-processing-tf-test-2"
  location              = var.region
  image                 = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/processing:latest"
  service_account_email = var.service_account_email
  template_annotations  = var.template_annotations
  container_concurrency = 10
  limits                = {
    cpu    = "1000m"
    memory = "512Mi"
  }
  env_vars = [
    {
      name  = "ENV"
      value = var.environment
    }
  ]
  env_secret_vars = [
    for secret_name in [
      "GCP_PROJECT_ID"
    ] : {
      name      = secret_name
      value_from = [
        {
          secret_key_ref = {
            name = secret_name
            key  = "latest"
          }
        }
      ]
    }
  ]
}

resource "google_cloud_run_service_iam_member" "public_access_service_processing" {
  location = module.service_processing.location
  service  = module.service_processing.service_name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
