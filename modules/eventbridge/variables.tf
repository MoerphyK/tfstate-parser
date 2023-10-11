variable "compliance_sfn_arn" {
  type        = string
  description = "The ARN of the State Machine to use for compliance"
}

variable "create_report_lambda_arn" {
  type        = string
  description = "The ARN of the Lambda function to use for creating reports"
}

variable "create_report_lambda_name" {
  type        = string
  description = "The name of the Lambda function to use for creating reports"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}