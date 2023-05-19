resource "aws_kms_key" "key" {
  description             = "${var.resource_prefix} - TFState Parser"
  deletion_window_in_days = 7
  tags                    = var.tags
}

resource "aws_kms_alias" "key_alias" {
  name          = "alias/tfstate-parser-key"
  target_key_id = aws_kms_key.key.key_id
}