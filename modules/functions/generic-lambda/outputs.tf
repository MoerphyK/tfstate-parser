output "lambda_arn" {
  value = aws_lambda_function.lambda_function.arn
  description = "The ARN of the Lambda function"
}

output "lambda_name" {
  value = aws_lambda_function.lambda_function.id
  description = "The name of the Lambda function"
}