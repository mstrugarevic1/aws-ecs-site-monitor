resource "aws_dynamodb_table" "monitors" {
  name         = "${var.name_prefix}-monitors"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "monitor_id"

  attribute {
    name = "monitor_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }
}

resource "aws_dynamodb_table" "check_results" {
  name         = "${var.name_prefix}-check-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "monitor_id"
  range_key    = "checked_at"

  attribute {
    name = "monitor_id"
    type = "S"
  }

  attribute {
    name = "checked_at"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }
}

