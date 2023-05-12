data "aws_iam_policy_document" "lambda_assume_role_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_kms_access_policy_document" {
  statement {
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    resources = ["*"]
  }
}

data "aws_iam_policy_document" "lambda_log_access_policy_document" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["${aws_cloudwatch_log_group.lambda_log_group.arn}:*"]
  }
}

// Lambda execution role
resource "aws_iam_role" "lambda_execution_role" {
  name               = "${var.function_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy_document.json
  description        = "Role for lambda task execution"
  tags               = var.tags
}

// Create all the policies we have documents for
resource "aws_iam_policy" "lambda_exec_role_policy" {
  for_each = { for policy in local.exec_role_policy_documents : policy.name => policy }
  name     = "${var.function_name}-${each.value.name}-policy"
  path     = "/"
  policy   = each.value.json
  tags     = var.tags
}

// Attach all created policies to the execution role
resource "aws_iam_role_policy_attachment" "attach_lambda_log_access_policy" {
  for_each   = aws_iam_policy.lambda_exec_role_policy
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = each.value.arn
}

// When deployed in VPC, we'll need the lambda permissions to access vpc resources
// Attach the managed policy conditionally
resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole" {
  ## TODO:: Issue occured while creating the module "delete_registration_lambda" from scratch 
  ##        using the target command to prevent the replacement of the API URL
  count      = var.vpc == null ? 0 : 1
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}