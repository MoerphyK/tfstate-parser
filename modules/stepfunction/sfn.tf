locals {
  sfn_name = "${var.resource_prefix}-sfn-create-registration"
}

data "template_file" "sfn" {
  template = file("${path.module}/sfn.json")
  vars     = var.functions
}

resource "aws_sfn_state_machine" "sfn_state_machine" {
  name       = local.sfn_name
  role_arn   = aws_iam_role.sfn_execution_role.arn
  definition = data.template_file.sfn.rendered
  tags       = var.tags
}