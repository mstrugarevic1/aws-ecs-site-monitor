output "monitors_table_name" {
  value = aws_dynamodb_table.monitors.name
}

output "monitors_table_arn" {
  value = aws_dynamodb_table.monitors.arn
}

output "check_results_table_name" {
  value = aws_dynamodb_table.check_results.name
}

output "check_results_table_arn" {
  value = aws_dynamodb_table.check_results.arn
}

