locals {
  tmp_build_path = "${path.module}/build/${var.function_name}.zip"
  exec_role_policy_documents = concat([
    {
      "name" : "log-access",
      "json" : data.aws_iam_policy_document.lambda_log_access_policy_document.json
    },
    {
      "name" : "kms-access",
      "json" : data.aws_iam_policy_document.lambda_kms_access_policy_document.json
    }
    ],
  var.execution_role_policies)
}