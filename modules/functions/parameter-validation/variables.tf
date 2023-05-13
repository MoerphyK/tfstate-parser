variable "function_name" {
  type        = string
  description = "Name of the function. Will be used as prefix for all related resources. Should not contain white spaces"
  default     = "parameter-validation"
}

variable "s3_source_bucket" {
  type        = string
  description = "Bucket to upload the source code to/fetch the source code from"
}

variable "layers" {
  type        = list(string)
  description = "Layers (arns) that should be attached to the lambda"
}

variable "tfe_token_arn" {
  type        = string
  description = "ARN of the secretsmanager secret to connect to the tfe api"
}

variable "tfe_endpoint" {
  type        = string
  description = "endpoint for the post /create /update tfe CMDB CI VM instance"
}


variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}