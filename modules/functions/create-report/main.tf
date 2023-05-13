data "aws_iam_policy_document" "s3_reporting_access_policy_document" {
  statement {
    actions = [
      "s3:*"
    ]

    resources = ["arn:aws:s3:::${var.reporting_bucket}", "arn:aws:s3:::${var.reporting_bucket}/*"]
  }
}

module "generic_lambda" {
  source           = "../generic-lambda"
  function_name    = "${var.resource_prefix}-${var.function_name}"
  s3_source_bucket = var.s3_source_bucket
  source_dir       = "${path.module}/src"

  execution_role_policies = [
    {
      "name" = "report-s3-access"
      "json" = data.aws_iam_policy_document.s3_reporting_access_policy_document.json
    }
  ]

  environment = {
    REPORTING_BUCKET = var.reporting_bucket
  }

  tags            = var.tags
  resource_prefix = var.resource_prefix
  layers          = var.layers
}