#################
#### Network ####
#################

#################
#### Storage ####
#################

module "s3" {
  source            = "./modules/s3-buckets"
  encryption_key_id = module.kms.key_id

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "secrets" {
  source = "./modules/secrets"

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "kms" {
  source = "./modules/kms"

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

######################
#### Stepfunction ####
######################

module "stepfunction" {
  source = "./modules/stepfunction"
  functions = {
    parameter-validation = module.parameter-validation.lambda_arn
    rules-to-org         = module.rules-to-org.lambda_arn
    get-workspaces       = module.get-workspaces.lambda_arn
    rules-to-workspace   = module.rules-to-workspace.lambda_arn
    apply-rules          = module.apply-rules.lambda_arn
    create-report        = module.create-report.lambda_arn
  }

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

#################
#### Lambdas ####
#################

module "default-layer" {
  source           = "./modules/layers/default-lambda-libs"
  s3_source_bucket = module.s3.lambda_source_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "parameter-validation" {
  source           = "./modules/functions/parameter-validation"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint      = var.tfe_endpoint
  tfe_auth_endpoint = var.tfe_auth_endpoint
  tfe_token_arn     = module.secrets.tfe_token_arn

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "rules-to-org" {
  source       = "./modules/functions/rules-to-org"
  rules_bucket = module.s3.rules_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "get-workspaces" {
  source = "./modules/functions/get-workspaces"
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint      = var.tfe_endpoint
  tfe_auth_endpoint = var.tfe_auth_endpoint
  tfe_token_arn     = module.secrets.tfe_token_arn

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "rules-to-workspace" {
  source = "./modules/functions/rules-to-workspace"
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint      = var.tfe_endpoint
  tfe_auth_endpoint = var.tfe_auth_endpoint
  tfe_token_arn     = module.secrets.tfe_token_arn

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "apply-rules" {
  source = "./modules/functions/apply-rules"
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint      = var.tfe_endpoint
  tfe_auth_endpoint = var.tfe_auth_endpoint
  tfe_token_arn     = module.secrets.tfe_token_arn
  rules_bucket      = module.s3.rules_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

module "create-report" {
  source        = "./modules/functions/create-report"
  report_bucket = module.s3.report_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}