output "layer_arn" {
  value = aws_lambda_layer_version.lambda_layer.arn
  description = "The ARN of the Lambda layer"
}