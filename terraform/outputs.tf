output "cloud_run_service_urls" {
  value = module.cloud_run.service_urls
}

output "cloud_storage_buckets" {
  value = module.cloud_storage.buckets
}

output "service_accounts" {
  value = module.service_account.service_accounts
}
