variable "service_account_groups" {
  description = "A list of service account groups, each with a prefix, service accounts, and roles"
  type = list(object({
    prefix            = string
    service_accounts  = list(string)
    project_roles     = list(string)
  }))
}
variable "project_id" {}
