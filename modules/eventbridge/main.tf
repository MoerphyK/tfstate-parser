################################################
#### Report Creation after Compliance Check ####
################################################

# CloudWatch Event Rule to trigger the Lambda function
resource "aws_cloudwatch_event_rule" "step_function_success_rule" {
  name        = "${var.resource_prefix}-sfn-success-rule"
  description = "Rule to trigger Lambda function on Step Function success"

  event_pattern = <<EOF
{
  "source": ["aws.states"],
  "detail-type": ["Step Functions Execution Status Change"],
  "detail": {
    "status": ["SUCCEEDED"],
    "stateMachineArn": ["${var.compliance_sfn_arn}"]
  }
}
EOF

  tags = var.tags
}

# CloudWatch Event Target to invoke the Lambda function
resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.step_function_success_rule.name
  target_id = "${var.resource_prefix}-invoke-report-creation-lambda"

  arn = var.create_report_lambda_arn
}

# IAM policy to allow CloudWatch Events to invoke the Lambda function
resource "aws_lambda_permission" "eventbridge_invoke_permission" {
  statement_id  = "AllowEventBridgeInvocation"
  action        = "lambda:InvokeFunction"
  function_name = var.create_report_lambda_name
  principal     = "events.amazonaws.com"

  source_arn = aws_cloudwatch_event_rule.step_function_success_rule.arn
}

################################################
#### Cronjob to trigger Compliance Check #######
################################################

# CloudWatch Event Rule to trigger the Step Function
resource "aws_cloudwatch_event_rule" "cronjob_rule" {
  name                = "${var.resource_prefix}-cronjob-rule"
  description         = "Rule to trigger the 'Compliance Checker' Step Function on a schedule"
  schedule_expression = "cron(0 6 * * ? *)"
  tags                = var.tags
}

# CloudWatch Event Target to invoke the Step Function
resource "aws_cloudwatch_event_target" "invoke_sfn" {
  rule      = aws_cloudwatch_event_rule.cronjob_rule.name
  target_id = "${var.resource_prefix}-invoke-compliance-sfn"
  arn       = var.compliance_sfn_arn
  role_arn  = aws_iam_role.cloudwatch_sfn_role.arn
}

# IAM role and policy to allow CloudWatch Events to start the Step Function
resource "aws_iam_role" "cloudwatch_sfn_role" {
  name = "${var.resource_prefix}-cloudwatch-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy to allow CloudWatch Events to start the Step Function
resource "aws_iam_role_policy" "cloudwatch_sfn_policy" {
  name = "${var.resource_prefix}-cloudwatch-sfn-policy"
  role = aws_iam_role.cloudwatch_sfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "states:StartExecution"
        Effect   = "Allow"
        Resource = var.compliance_sfn_arn
      }
    ]
  })
}