data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "s3_rules_access_policy_document" {
  statement {
    actions = [
      "s3:*"
    ]

    resources = ["arn:aws:s3:::${var.rules_bucket}", "arn:aws:s3:::${var.rules_bucket}/*"]
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
      "name" = "rules-s3-access"
      "json" = data.aws_iam_policy_document.s3_rules_access_policy_document.json
    },
    {
      "name" = "rules-ddb-access"
      "json" = data.aws_iam_policy_document.ddb_rules_access_policy_document.json
    }
  ]

  environment = {
    RULES_BUCKET = var.rules_bucket
    RULES_TABLE  = var.rules_table
  }

  tags            = var.tags
  resource_prefix = var.resource_prefix
  layers          = var.layers
}


# Create the S3 notification for the rules bucket
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.rules_bucket

  lambda_function {
    lambda_function_arn = module.generic_lambda.lambda_arn
    events              = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.generic_lambda.lambda_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.rules_bucket}"
}