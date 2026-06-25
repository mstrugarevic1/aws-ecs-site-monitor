variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_account_id" {
  type        = string
  default     = ""
  description = "Future deployment account ID. Leave empty during local validation."
}

variable "name_prefix" {
  type    = string
  default = "aws-ecs-internal-service-monitor-dev"
}

variable "image_uri" {
  type        = string
  default     = "aws-ecs-internal-service-monitor:local"
  description = "Future immutable ECR image URI tagged with a Git SHA."
}

variable "notification_email" {
  type        = string
  default     = ""
  description = "Optional future SNS email subscription. Do not commit personal email addresses."
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "result_ttl_days" {
  type    = number
  default = 7
}

