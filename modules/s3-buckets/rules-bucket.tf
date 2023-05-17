resource "aws_s3_bucket" "rules_bucket" {
  bucket = "${var.resource_prefix}-rules"
  tags   = var.tags
}

resource "aws_s3_bucket_public_access_block" "rules_bucket_access_block" {
  bucket = aws_s3_bucket.rules_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# resource "aws_s3_bucket_acl" "rules_acl" {
#   bucket = aws_s3_bucket.rules_bucket.id
#   acl    = "private"
# }

resource "aws_s3_bucket_server_side_encryption_configuration" "rules_encryption" {
  bucket = aws_s3_bucket.rules_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.encryption_key_id
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_object" "object" {
  for_each = toset( ["AWS/DEV", "AWS/QA", "AWS/PROD","AZURE/DEV", "AZURE/QA", "AZURE/PROD"] )
  bucket = aws_s3_bucket.rules_bucket.id
  key    = "ALL/${each.key}/"
}

# For testing purposes
resource "aws_s3_object" "ago_keys" {
  for_each = toset( ["AWS/DEV", "AWS/QA", "AWS/PROD","AZURE/DEV", "AZURE/QA", "AZURE/PROD"] )
  bucket = aws_s3_bucket.rules_bucket.id
  key    = "AGO/${each.key}/"
}