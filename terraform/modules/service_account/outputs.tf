output "service_accounts" {
  value = { for k, v in module.accounts : k => v.email }
}
