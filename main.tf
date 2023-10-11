#################
#### Storage ####
#################

# Create a bucket for the lambda source code
module "s3" {
  source            = "./modules/s3-buckets"
  encryption_key_id = module.kms.key_id

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a dynamodb table to store the rules
module "dynamodb" {
  source = "./modules/dynamodb-tables"

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create secrets in AWS Secrets Manager for the TFE token
module "secrets" {
  source = "./modules/secrets"

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a KMS key to encrypt the secrets
module "kms" {
  source = "./modules/kms"

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

######################
#### Stepfunction ####
######################

# Create a step function to run the compliance checks
module "stepfunction" {
  source = "./modules/stepfunction"
  functions = {
    get-organizations  = module.get-organizations.lambda_arn
    get-workspaces     = module.get-workspaces.lambda_arn
    rules-to-workspace = module.rules-to-workspace.lambda_arn
  }

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

#################
#### Lambdas ####
#################

# Create a Lambda function to get the organizations
module "get-organizations" {
  source           = "./modules/functions/get-organizations"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint  = var.tfe_endpoint
  tfe_token_arn = module.secrets.tfe_token_arn

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a Lambda function to get the workspaces
module "get-workspaces" {
  source           = "./modules/functions/get-workspaces"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint  = var.tfe_endpoint
  tfe_token_arn = module.secrets.tfe_token_arn

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a Lambda function to get the rules
module "rules-to-workspace" {
  source           = "./modules/functions/rules-to-workspace"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  tfe_endpoint     = var.tfe_endpoint
  tfe_token_arn    = module.secrets.tfe_token_arn
  rules_table      = module.dynamodb.rules_table
  reporting_bucket = module.s3.reporting_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a Lambda function to create the report
module "create-report" {
  source           = "./modules/functions/create-report"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  reporting_bucket = module.s3.reporting_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a Lambda function to create the rule table entry
module "create-rule-table-entry" {
  source           = "./modules/functions/create-rule-table-entry"
  s3_source_bucket = module.s3.lambda_source_bucket
  layers = [
    module.default-layer.layer_arn
  ]
  rules_bucket = module.s3.rules_bucket
  rules_table  = module.dynamodb.rules_table

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

##############
#### MISC ####
##############

# Configure the eventbridge to trigger the step function
module "eventbridge" {
  source                    = "./modules/eventbridge"
  compliance_sfn_arn        = module.stepfunction.sfn_arn
  create_report_lambda_arn  = module.create-report.lambda_arn
  create_report_lambda_name = module.create-report.lambda_name

  resource_prefix = var.resource_prefix
  tags            = var.tags
}

# Create a lambda layer with the default libraries
module "default-layer" {
  source           = "./modules/layers/default-lambda-libs"
  s3_source_bucket = module.s3.lambda_source_bucket

  resource_prefix = var.resource_prefix
  tags            = var.tags
}