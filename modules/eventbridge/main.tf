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

resource "aws_cloudwatch_event_target" "invoke_lambda" {
  rule      = aws_cloudwatch_event_rule.step_function_success_rule.name
  target_id = "${var.resource_prefix}-invoke-report-creation-lambda"

  arn = var.create_report_lambda_arn
}

resource "aws_lambda_permission" "eventbridge_invoke_permission" {
  statement_id  = "AllowEventBridgeInvocation"
  action        = "lambda:InvokeFunction"
  function_name = var.create_report_lambda_name
  principal     = "events.amazonaws.com"

  source_arn = aws_cloudwatch_event_rule.step_function_success_rule.arn
}