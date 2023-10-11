variable "s3_source_bucket" {
  type = string
  description = "The name of the S3 bucket used to store Lambda source packages"
}

variable "lambda_layer_name" {
  type    = string
  default = "default-libs"
  description = "The name of the Lambda layer"
}

variable "function_runtime" {
  type    = string
  default = "python3.8"
  description = "The runtime for the Lambda function"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}