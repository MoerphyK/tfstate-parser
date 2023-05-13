data "aws_iam_policy_document" "lambda_secret_access_policy_document" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [var.tfe_token_arn]
  }
}

module "generic_lambda" {
  source           = "../generic-lambda"
  function_name    = "${var.resource_prefix}-validate-parameters"
  s3_source_bucket = var.s3_source_bucket
  source_dir       = "${path.module}/src"

  execution_role_policies = [
    {
      "name" = "secrets-access"
      "json" = data.aws_iam_policy_document.lambda_secret_access_policy_document.json
    }
  ]

  environment = {
    TFE_TOKEN_CREDENTIALS = var.tfe_token_arn,
    TFE_ENDPOINT          = var.tfe_endpoint
  }

  tags            = var.tags
  resource_prefix = var.resource_prefix
  layers          = var.layers
}