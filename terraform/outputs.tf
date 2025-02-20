output "service_check_respondent_identity_url" {
  value       = module.service_check_respondent_identity.service_url
  description = "The URL on which the service 'service_check_respondent_identity' is available"
}

output "service_processing_url" {
  value       = module.service_processing.service_url
  description = "The URL on which the service 'service_processing' is available"
}
