output "lambda_arn" {
  value = module.generic_lambda.lambda_arn
  description = "The ARN of the Lambda function"
}

output "lambda_name" {
  value = module.generic_lambda.lambda_name
  description = "The name of the Lambda function"
}