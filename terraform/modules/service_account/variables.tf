variable "service_account_groups" {
  description = "A list of service account groups, each with a prefix, service accounts, and roles"
  type = list(object({
    prefix            = string
    service_accounts  = list(string)
    project_roles     = list(string)
  }))
}

variable "resource_roles" {
  description = "List of resource-specific roles with their target resource."
  type = list(object({
    service_account = string # Email of the service account
    role            = string # IAM Role
    resources       = list(string) # List of target resources (Cloud Run, Pub/Sub, etc.)
    type            = string # Resource type (e.g., "cloud_run", "pubsub", "storage")
    region          = string
  }))
  default = []
}

variable "project_id" {}
