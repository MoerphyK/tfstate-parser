output "lambda_source_bucket" {
  value = aws_s3_bucket.lambda_source_bucket.id
}

output "reporting_bucket" {
  value = aws_s3_bucket.reporting_bucket.id
}