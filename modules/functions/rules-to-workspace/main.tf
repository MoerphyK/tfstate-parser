data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "lambda_secret_access_policy_document" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [var.tfe_token_arn]
  }
}

data "aws_iam_policy_document" "s3_reporting_access_policy_document" {
  statement {
    actions = [
      "s3:*"
    ]

    resources = ["arn:aws:s3:::${var.reporting_bucket}", "arn:aws:s3:::${var.reporting_bucket}/*"]
  }
}

data "aws_iam_policy_document" "ddb_rules_access_policy_document" {
  statement {
    actions = [
      "dynamodb:*"
    ]

    resources = ["arn:aws:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${var.rules_table}"]
  }
}

module "generic_lambda" {
  source           = "../generic-lambda"
  function_name    = "${var.resource_prefix}-${var.function_name}"
  s3_source_bucket = var.s3_source_bucket
  source_dir       = "${path.module}/src"

  execution_role_policies = [
    {
      "name" = "secrets-access"
      "json" = data.aws_iam_policy_document.lambda_secret_access_policy_document.json
    },
    {
      "name" = "rules-s3-access"
      "json" = data.aws_iam_policy_document.s3_reporting_access_policy_document.json
    },
    {
      "name" = "rules-ddb-access"
      "json" = data.aws_iam_policy_document.ddb_rules_access_policy_document.json
    }
  ]

  environment = {
    RULES_TABLE           = var.rules_table,
    REPORTING_BUCKET      = var.reporting_bucket,
    TFE_TOKEN_CREDENTIALS = var.tfe_token_arn,
    TFE_ENDPOINT          = var.tfe_endpoint
  }

  tags            = var.tags
  resource_prefix = var.resource_prefix
  layers          = var.layers
}