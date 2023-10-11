output "rules_table" {
  value = aws_dynamodb_table.rules_table.id
  description = "The name of the DynamoDB table used to store rules data"
}