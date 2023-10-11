# Create S3 bucket for Lambda source packages
resource "aws_s3_bucket" "lambda_source_bucket" {
  bucket = "${var.resource_prefix}-lambda-source-packages"
  tags   = var.tags
}

# Configure bucket to block public access
resource "aws_s3_bucket_public_access_block" "lambda_source_bucket_access_block" {
  bucket = aws_s3_bucket.lambda_source_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Configure bucket versioning
resource "aws_s3_bucket_versioning" "lambda_source_versioning" {
  bucket = aws_s3_bucket.lambda_source_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Configure bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_source_encryption" {
  bucket = aws_s3_bucket.lambda_source_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}