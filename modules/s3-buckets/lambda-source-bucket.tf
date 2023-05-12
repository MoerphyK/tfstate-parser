resource "aws_s3_bucket" "lambda_source_bucket" {
  bucket = "${var.resource_prefix}-lambda-source-packages"
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "lambda_source_bucket_access_block" {
  bucket = aws_s3_bucket.lambda_source_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_acl" "lambda_source_acl" {
  bucket = aws_s3_bucket.lambda_source_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_versioning" "lambda_source_versioning" {
  bucket = aws_s3_bucket.lambda_source_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_source_encryption" {
  bucket = aws_s3_bucket.lambda_source_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}