output "tfe_token_arn" {
  value = aws_secretsmanager_secret.tfe_token.arn
  description = "The ARN of the TFE token secret"
}