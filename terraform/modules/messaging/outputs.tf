output "queue_url" {
  value = aws_sqs_queue.checks.url
}

output "queue_name" {
  value = aws_sqs_queue.checks.name
}

output "queue_arn" {
  value = aws_sqs_queue.checks.arn
}

output "dlq_name" {
  value = aws_sqs_queue.dead_letter.name
}

output "dlq_arn" {
  value = aws_sqs_queue.dead_letter.arn
}

output "alerts_topic_arn" {
  value = aws_sns_topic.alerts.arn
}
