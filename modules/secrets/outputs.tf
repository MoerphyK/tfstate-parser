output "puppet_api_credentials_arn" {
  value = aws_secretsmanager_secret.puppet_api_credentials.arn
}

output "puppet_api_credentials_id" {
  value = aws_secretsmanager_secret.puppet_api_credentials.id
}

output "silva_api_credentials_arn" {
  value = aws_secretsmanager_secret.silva_api_credentials.arn
}

output "silva_api_credentials_id" {
  value = aws_secretsmanager_secret.silva_api_credentials.id
}

output "silva_incident_api_credentials_arn" {
  value = aws_secretsmanager_secret.silva_incident_api_credentials.arn
}

output "silva_axalis_api_credentials_arn" {
  value = aws_secretsmanager_secret.silva_axalis_api_credentials.arn
}

output "lisa_api_credentials_arn" {
  value = aws_secretsmanager_secret.lisa_api_credentials.arn
}

output "lisa_api_credentials_id" {
  value = aws_secretsmanager_secret.lisa_api_credentials.id
}

output "axa_mailserver_credentials_arn" {
  value = aws_secretsmanager_secret.axa_mailserver_credentials.arn
}

output "axa_mailserver_credentials_id" {
  value = aws_secretsmanager_secret.axa_mailserver_credentials.id
}