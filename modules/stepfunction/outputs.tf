output "sfn_id" {
  value = aws_sfn_state_machine.sfn_state_machine.id
  description = "The ID of the state machine"
}

output "sfn_arn" {
  value = aws_sfn_state_machine.sfn_state_machine.arn
  description = "The ARN of the state machine"
}