output "key_id" {
  value = aws_kms_key.key.arn
  description = "The ARN of the KMS key"
}