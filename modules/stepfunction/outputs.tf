output "sfn_id" {
  value = aws_sfn_state_machine.sfn_state_machine.id
}

output "sfn_arn" {
  value = aws_sfn_state_machine.sfn_state_machine.arn
}