output "service_check_respondent_identity_url" {
  value       = module.service_check_respondent_identity.service_url
  description = "The URL on which the service 'service_check_respondent_identity' is available"
}

output "service_processing_url" {
  value       = module.service_processing.service_url
  description = "The URL on which the service 'service_processing' is available"
}

output "service_study_administrator_url" {
  value       = module.service_study_administrator.service_url
  description = "The URL on which the service 'study_administrator' is available"
}

output "service_accounts_storage_email" {
  value       = module.service_accounts_storage.email
  description = "The email of the created service account"
}

output "cloud_storage_buckets_urls" {
  value       = module.cloud_storage_buckets.urls
  description = "The URLs of the created buckets"
}
