module "accounts" {
  source  = "terraform-google-modules/service-accounts/google"
  version = "~> 4.0"

  for_each      = { for group in var.service_account_groups : group.service_accounts[0] => group }
  project_id    = var.project_id
  prefix        = each.value.prefix
  names         = each.value.service_accounts
  project_roles = each.value.project_roles
}
