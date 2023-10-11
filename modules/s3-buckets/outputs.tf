output "lambda_source_bucket" {
  value = aws_s3_bucket.lambda_source_bucket.id
  description = "The name of the S3 bucket used to store Lambda source packages"
}

output "reporting_bucket" {
  value = aws_s3_bucket.reporting_bucket.id
  description = "The name of the S3 bucket used to store reporting data"
}

output "rules_bucket" {
  value = aws_s3_bucket.rules_bucket.id
  description = "The name of the S3 bucket used to store rules data"
}