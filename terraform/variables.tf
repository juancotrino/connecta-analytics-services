variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (e.g., dev, staging, prod)"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for the Cloud Run service"
  type        = string
}

variable "secrets" {
  description = "List of secrets to inject as environment variables"
  type = list(object({
    secret  = string
    version = string
  }))
  default = []
}

variable "template_annotations" {
  description = "Minimum and maximum scaling options and other options"
  type = map(number)
  default = {
    "autoscaling.knative.dev/minScale" = 0
    "autoscaling.knative.dev/maxScale" = 5
  }
}

variable "changed_services" {
  description = "List of services that need to be deployed"
  type        = list(string)
}
