output "lambda_source_bucket" {
  value = aws_s3_bucket.lambda_source_bucket.id
}

output "reporting_bucket" {
  value = aws_s3_bucket.reporting_bucket.id
}

output "rules_bucket" {
  value = aws_s3_bucket.rules_bucket.id
}