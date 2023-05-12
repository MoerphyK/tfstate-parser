data "aws_iam_policy_document" "sfn_access_policy_document" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [for k, v in var.functions : v]
  }
}

data "aws_iam_policy_document" "sfn_assume_role_policy_document" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sfn_execution_role" {
  name               = "${local.sfn_name}-execution-role"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role_policy_document.json
  description        = "Role for sfn task execution"
  tags               = var.tags
}

resource "aws_iam_policy" "sfn_access_policy" {
  name        = "${local.sfn_name}-access-policy"
  path        = "/"
  description = "IAM policy to grant sfn access"
  policy      = data.aws_iam_policy_document.sfn_access_policy_document.json
  tags        = var.tags
}

resource "aws_iam_role_policy_attachment" "attach_sfn_access_policy" {
  role       = aws_iam_role.sfn_execution_role.name
  policy_arn = aws_iam_policy.sfn_access_policy.arn
}