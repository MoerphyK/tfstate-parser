resource "aws_dynamodb_table" "rules_table" {
  name           = "${var.resource_prefix}-rules"
  read_capacity  = 20
  write_capacity = 20
  hash_key       = "S3Key"
  range_key      = "ResourceType"

  attribute {
    name = "S3Key"
    type = "S"
  }

  attribute {
    name = "ResourceType"
    type = "S"
  }

  tags = var.tags
}