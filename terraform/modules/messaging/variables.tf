variable "name_prefix" {
  type = string
}

variable "notification_email" {
  type    = string
  default = ""
}

variable "visibility_timeout_seconds" {
  type    = number
  default = 60
}

