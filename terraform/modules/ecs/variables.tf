variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "image_uri" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "api_security_group_id" {
  type = string
}

variable "worker_security_group_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "monitors_table_arn" {
  type = string
}

variable "check_results_table_arn" {
  type = string
}

variable "queue_arn" {
  type = string
}

variable "queue_url" {
  type = string
}

variable "alerts_topic_arn" {
  type = string
}

variable "api_desired_count" {
  type    = number
  default = 1
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "log_retention_days" {
  type    = number
  default = 7
}

