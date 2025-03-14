locals {
  # Generate Cloud Run service names dynamically from bucket names
  services_map = { for service in var.services_names : service => "${var.project_id}-service-${service}" }
}

resource "google_eventarc_trigger" "main" {
  for_each = local.services_map

  name     = "trigger-storage-${each.key}"
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = each.value
  }

  destination {
    cloud_run_service {
      service = "service-${each.key}"  # Cloud Run service name
      path    = "/get_from_storage"
      region  = var.region
    }
  }

  service_account = var.service_account_email
}
