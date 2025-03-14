variable "services" {
  type = list(object({
    name                  = string
    image                 = string
    memory                = string
    cpu                   = string
    service_account_email = string
    template_annotations  = map(number)
    secrets               = list(string)
  }))
  description = "List of Cloud Run services to create"
}

variable "project_id" {}
variable "region" {}
variable "environment" {}
