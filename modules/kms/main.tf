resource "aws_kms_key" "key" {
  description             = "${var.resource_prefix} - TFState Parser"
  deletion_window_in_days = 7
  tags                    = var.tags
}