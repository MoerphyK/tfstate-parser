###############################
##### Version Constraints #####
###############################

terraform {
  required_providers {
    archive = {
      source = "hashicorp/archive"
      version = "2.3.0"
    }
  }
}

resource "aws_lambda_function" "lambda_function" {
  depends_on = [aws_iam_role_policy_attachment.AWSLambdaVPCAccessExecutionRole]
  function_name     = var.function_name
  handler           = var.function_handler
  runtime           = var.function_runtime
  role              = aws_iam_role.lambda_execution_role.arn
  timeout           = var.function_timeout
  s3_bucket         = var.s3_source_bucket
  s3_key            = aws_s3_object.object.id
  s3_object_version = aws_s3_object.object.version_id

  layers = var.layers

  environment {
    variables = var.environment
  }

  dynamic "vpc_config" {
    for_each = var.vpc == null ? [] : [1]
    content {
      security_group_ids = var.vpc.security_group_ids
      subnet_ids         = var.vpc.subnet_ids
    }
  }

  tags = var.tags
}