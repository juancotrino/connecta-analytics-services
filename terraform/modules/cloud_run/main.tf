module "services" {
  source  = "GoogleCloudPlatform/cloud-run/google"
  version = "~> 0.10.0"

  for_each = { for service in var.services : service.name => service }

  project_id            = var.project_id
  service_name          = each.value.name
  location              = var.region
  image                 = each.value.image
  service_account_email = each.value.service_account_email
  template_annotations  = each.value.template_annotations
  container_concurrency = 10

  limits = {
    cpu    = each.value.cpu
    memory = each.value.memory
  }

  env_vars = [
    {
      name  = "ENV"
      value = var.environment
    }
  ]

  env_secret_vars = [
    for secret_name in each.value.secrets : {
      name      = secret_name
      value_from = [{
        secret_key_ref = {
          name = secret_name
          key  = "latest"
        }
      }]
    }
  ]
}

resource "google_cloud_run_service_iam_member" "public_access" {
  for_each = module.services

  location = each.value.location
  service  = each.value.service_name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
