output "ecr_repository_url" {
  value = module.ecr.repository_url
}

output "alb_dns_name" {
  value = module.ecs.alb_dns_name
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "api_service_name" {
  value = module.ecs.api_service_name
}

output "worker_service_name" {
  value = module.ecs.worker_service_name
}

output "dashboard_name" {
  value = module.observability.dashboard_name
}

output "api_task_role_arn" {
  value = module.ecs.api_task_role_arn
}

output "scheduler_task_role_arn" {
  value = module.ecs.scheduler_task_role_arn
}

output "worker_task_role_arn" {
  value = module.ecs.worker_task_role_arn
}
