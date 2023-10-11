# Create a S3 bucket for the Compliance Checker results and reports
resource "aws_s3_bucket" "reporting_bucket" {
  bucket = "${var.resource_prefix}-reports"
  tags   = var.tags
}

# Configure bucket to block public access
resource "aws_s3_bucket_public_access_block" "reporting_bucket_access_block" {
  bucket = aws_s3_bucket.reporting_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "reporting_encryption" {
  bucket = aws_s3_bucket.reporting_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}