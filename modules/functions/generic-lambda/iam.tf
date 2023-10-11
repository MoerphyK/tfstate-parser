# Create a policy document that defines the IAM role for the lambda
data "aws_iam_policy_document" "lambda_assume_role_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# Create a policy document that allows the lambda to access the KMS key
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

# Create a policy document that allows the lambda to log to CloudWatch
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

# Create an IAM role for the Lambda function
resource "aws_iam_role" "lambda_execution_role" {
  name               = "${var.function_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy_document.json
  description        = "Role for lambda task execution"
  tags               = var.tags
}

# Create a policies for the Lambda function 
resource "aws_iam_policy" "lambda_exec_role_policy" {
  for_each = { for policy in local.exec_role_policy_documents : policy.name => policy }
  name     = "${var.function_name}-${each.value.name}-policy"
  path     = "/"
  policy   = each.value.json
  tags     = var.tags
}

# Attach the log access policy to the role
resource "aws_iam_role_policy_attachment" "attach_lambda_log_access_policy" {
  for_each   = aws_iam_policy.lambda_exec_role_policy
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = each.value.arn
}

# Attach a VPC policies to the Lambda role, if a VPC is specified 
resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole" {
  ## TODO:: Issue occured while creating the module "delete_registration_lambda" from scratch 
  ##        using the target command to prevent the replacement of the API URL
  count      = var.vpc == null ? 0 : 1
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}