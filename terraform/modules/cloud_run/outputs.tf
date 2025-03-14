output "service_urls" {
  value = { for service in module.services : service.service_name => service.service_url }
}
