module "cloud_run" {
  source      = "./modules/cloud_run"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  services = [
    {
      name   = "service-check-respondent-identity"
      image  = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/check-respondent-identity:latest"
      cpu    = "1000m"
      memory = "256Mi"
      service_account_email = var.service_account_email
      template_annotations  = var.template_annotations
      secrets = [
        "GCP_PROJECT_ID",
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_SERVICE_SID"
      ]
    },
    {
      name   = "service-storage-proxy"
      image  = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/storage-proxy:latest"
      cpu    = "1000m"
      memory = "256Mi"
      service_account_email = var.service_account_email
      template_annotations  = var.template_annotations
      secrets = [
        "GCP_PROJECT_ID",
      ]
    },
    {
      name   = "service-processing"
      image  = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/processing:latest"
      cpu    = "1000m"
      memory = "512Mi"
      service_account_email = var.service_account_email
      template_annotations  = var.template_annotations
      secrets = [
        "GCP_PROJECT_ID"
      ]
    },
    {
      name   = "service-study-administrator"
      image  = "${var.region}-docker.pkg.dev/${var.project_id}/connecta-services/study-administrator:latest"
      cpu    = "1000m"
      memory = "256Mi"
      service_account_email = var.service_account_email
      template_annotations  = var.template_annotations
      secrets = [
        "GCP_PROJECT_ID"
      ]
    }
  ]
}


###############################################################################

# Grant the Cloud Storage service account permission to publish pub/sub topics
data "google_storage_project_service_account" "gcs_account" {}
resource "google_project_iam_member" "pubsubpublisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

module "cloud_storage" {
  source  = "terraform-google-modules/cloud-storage/google"
  version = "~> 9.1"

  project_id  = var.project_id
  names       = var.services_names # Use the variable here
  prefix      = "${var.project_id}-service"
  location    = var.region

  force_destroy = {
    for name in var.services_names : name => true
  }

  admins = [
    "serviceAccount:${module.service_account.service_accounts["service-storage-proxy"]}@${var.project_id}.iam.gserviceaccount.com"
  ]

  folders = {
    for name in var.services_names : name => ["landingzone", "processed", "archive"]
  }
}

############################################################################

module "service_account" {
  source     = "./modules/service_account"

  project_id = var.project_id
  service_account_groups = [
    {
      prefix = ""
      service_accounts = [split("@", var.service_account_email)[0]]
      project_roles = [
        "${var.project_id}=>roles/eventarc.eventReceiver",
        "${var.project_id}=>roles/aiplatform.user",
        "${var.project_id}=>roles/bigquery.user",
        "${var.project_id}=>roles/datastore.user",
        "${var.project_id}=>roles/firebaseauth.admin",
        "${var.project_id}=>roles/firebasestorage.admin",
        "${var.project_id}=>roles/iam.serviceAccountUser",
        "${var.project_id}=>roles/secretmanager.secretAccessor",
        "${var.project_id}=>roles/storage.objectUser"
      ]
    },
    {
      prefix = "sa"
      service_accounts = ["service-storage-proxy"]
      project_roles = ["${var.project_id}=>roles/storage.objectAdmin"]
    },
  ]
}

############################################################################

module "eventarc" {
  source = "./modules/eventarc"

  services_names        = ["processing"] # var.services_names
  project_id            = var.project_id
  region                = var.region
  service_account_email = var.service_account_email
}
