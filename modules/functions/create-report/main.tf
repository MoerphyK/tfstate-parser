data "aws_iam_policy_document" "s3_reporting_access_policy_document" {
  statement {
    actions = [
      "s3:*"
    ]

    resources = [var.reporting_bucket]
  }
}

module "generic_lambda" {
  source           = "../generic-lambda"
  function_name    = "${var.resource_prefix}-validate-parameters"
  s3_source_bucket = var.s3_source_bucket
  source_dir       = "${path.module}/src"

  execution_role_policies = [
    {
      "name" = "report-s3-access"
      "json" = data.aws_iam_policy_document.s3_reporting_access_policy_document.json
    }
  ]

  environment = {
    REPORTING_BUCKET  = var.reporting_bucket
  }

  tags            = var.tags
  resource_prefix = var.resource_prefix
  layers          = var.layers
}