# Creates the S3 bucket for the rules
resource "aws_s3_bucket" "rules_bucket" {
  bucket = "${var.resource_prefix}-rules"
  tags   = var.tags
}

# Configure bucket to block public access
resource "aws_s3_bucket_public_access_block" "rules_bucket_access_block" {
  bucket = aws_s3_bucket.rules_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "rules_encryption" {
  bucket = aws_s3_bucket.rules_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}

# Create a folder structure for the rules
resource "aws_s3_object" "object" {
  for_each = toset(["AWS/DEV", "AWS/QA", "AWS/PROD", "AWS/ALL", "AZURE/DEV", "AZURE/QA", "AZURE/PROD", "AZURE/ALL"])
  bucket   = aws_s3_bucket.rules_bucket.id
  key      = "ALL/${each.key}/"
}

resource "aws_s3_object" "ago_keys" {
  for_each = toset(["AWS/DEV", "AWS/QA", "AWS/PROD", "AWS/ALL", "AZURE/DEV", "AZURE/QA", "AZURE/PROD", "AZURE/ALL"])
  bucket   = aws_s3_bucket.rules_bucket.id
  key      = "AGO/${each.key}/"
}