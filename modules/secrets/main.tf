resource "aws_secretsmanager_secret" "puppet_api_credentials" {
  name                    = "${var.resource_prefix}-puppet-integration-credentials"
  description             = "Credentials to be used to access the puppet api for puppet integration"
  recovery_window_in_days = 0
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "silva_api_credentials" {
  name                    = "${var.resource_prefix}-silva-api-credentials"
  description             = "Credentials to be used to access the Silva api for CMDB VI creation"
  recovery_window_in_days = 0
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "silva_incident_api_credentials" {
  name                    = "${var.resource_prefix}-silva-incident-api-credentials"
  description             = "Credentials to be used to access the Silva api for incident creation"
  recovery_window_in_days = 0
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "silva_axalis_api_credentials" {
  name                    = "${var.resource_prefix}-silva-axalis-api-credentials"
  description             = "Credentials to be used to access the Silva api for axalis cmdb"
  recovery_window_in_days = 0
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "lisa_api_credentials" {
  name                    = "${var.resource_prefix}-lisa-api-credentials"
  description             = "Credentials to be used to access the LISA api"
  recovery_window_in_days = 0
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "axa_mailserver_credentials" {
  name                    = "${var.resource_prefix}-axa-mailserver-credentials"
  description             = "Credentials to be used to access the AXA mailserver"
  recovery_window_in_days = 0
  tags                    = var.tags
}