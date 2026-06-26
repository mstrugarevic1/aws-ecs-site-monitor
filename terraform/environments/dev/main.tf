module "networking" {
  source = "../../modules/networking"

  name_prefix         = var.name_prefix
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  availability_zones  = var.availability_zones
}

module "ecr" {
  source = "../../modules/ecr"

  name_prefix = var.name_prefix
}

module "database" {
  source = "../../modules/database"

  name_prefix     = var.name_prefix
  result_ttl_days = var.result_ttl_days
}

module "messaging" {
  source = "../../modules/messaging"

  name_prefix        = var.name_prefix
  notification_email = var.notification_email
}

module "ecs" {
  source = "../../modules/ecs"

  name_prefix              = var.name_prefix
  aws_region               = var.aws_region
  image_uri                = var.image_uri
  public_subnet_ids        = module.networking.public_subnet_ids
  alb_security_group_id    = module.networking.alb_security_group_id
  api_security_group_id    = module.networking.api_security_group_id
  worker_security_group_id = module.networking.worker_security_group_id
  vpc_id                   = module.networking.vpc_id
  monitors_table_arn       = module.database.monitors_table_arn
  monitors_table_name      = module.database.monitors_table_name
  check_results_table_arn  = module.database.check_results_table_arn
  check_results_table_name = module.database.check_results_table_name
  queue_arn                = module.messaging.queue_arn
  queue_url                = module.messaging.queue_url
  alerts_topic_arn         = module.messaging.alerts_topic_arn
}

module "observability" {
  source = "../../modules/observability"

  name_prefix             = var.name_prefix
  aws_region              = var.aws_region
  cluster_name            = module.ecs.cluster_name
  api_service_name        = module.ecs.api_service_name
  worker_service_name     = module.ecs.worker_service_name
  alb_name                = module.ecs.alb_name
  alb_arn_suffix          = module.ecs.alb_arn_suffix
  target_group_arn_suffix = module.ecs.target_group_arn_suffix
  queue_name              = module.messaging.queue_name
  dlq_name                = module.messaging.dlq_name
}
