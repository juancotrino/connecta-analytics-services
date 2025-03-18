module "accounts" {
  source  = "terraform-google-modules/service-accounts/google"
  version = "~> 4.0"

  for_each      = { for group in var.service_account_groups : group.service_accounts[0] => group }
  project_id    = var.project_id
  prefix        = each.value.prefix
  names         = each.value.service_accounts
  project_roles = each.value.project_roles
}

# Handle Resource-Level IAM Roles (Cloud Run example)
resource "google_cloud_run_service_iam_member" "cloud_run_roles" {
  for_each = { for r in flatten([
    for role in var.resource_roles : [
      for resource in role.resources : {
        key             = "${role.service_account}_${role.role}_${resource}"
        service_account = role.service_account
        role            = role.role
        resource        = "service-${resource}"
        type            = role.type
        region          = role.region
      }
    ]
  ]) : r.key => r if r.type == "cloud_run" }

  service  = each.value.resource
  location = each.value.region
  role     = each.value.role
  member   = "serviceAccount:${each.value.service_account}"
}
