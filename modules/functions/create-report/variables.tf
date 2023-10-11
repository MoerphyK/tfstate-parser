variable "function_name" {
  type        = string
  description = "Name of the function. Will be used as prefix for all related resources. Should not contain white spaces"
  default     = "create-report"
}

variable "s3_source_bucket" {
  type        = string
  description = "Bucket to upload the source code to/fetch the source code from"
}

variable "layers" {
  type        = list(string)
  description = "Layers (arns) that should be attached to the lambda"
}

variable "reporting_bucket" {
  type        = string
  description = "Bucket to upload the reports to"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}