output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "api_service_name" {
  value = aws_ecs_service.api.name
}

output "worker_service_name" {
  value = aws_ecs_service.worker.name
}

output "alb_name" {
  value = aws_lb.api.name
}

output "alb_arn_suffix" {
  value = aws_lb.api.arn_suffix
}

output "alb_dns_name" {
  value = aws_lb.api.dns_name
}

output "target_group_arn_suffix" {
  value = aws_lb_target_group.api.arn_suffix
}

output "api_task_role_arn" {
  value = aws_iam_role.api.arn
}

output "scheduler_task_role_arn" {
  value = aws_iam_role.scheduler.arn
}

output "worker_task_role_arn" {
  value = aws_iam_role.worker.arn
}
