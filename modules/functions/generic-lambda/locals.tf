locals {
  tmp_build_path = "${path.module}/build/${var.function_name}.zip"
  exec_role_policy_documents = concat([
    // Fixed policies, attached to all lambdas
    {
      "name" : "log-access",
      "json" : data.aws_iam_policy_document.lambda_log_access_policy_document.json
    },
    {
      "name" : "kms-access",
      "json" : data.aws_iam_policy_document.lambda_kms_access_policy_document.json
    }
    ],
    // User-passed policy documents
  var.execution_role_policies)
}