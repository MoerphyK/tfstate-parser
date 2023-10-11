# Create a secret for the TFE token
resource "aws_secretsmanager_secret" "tfe_token" {
  name                    = "${var.resource_prefix}-tfe-token"
  description             = "Credentials to be used to access the TFE api for tfstate parsing"
  recovery_window_in_days = 0
  tags                    = var.tags
}