variable "function_name" {
  type        = string
  description = "Name of the function. Will be used as prefix for all related resources. Should not contain white spaces"

  validation {
    condition     = can(regex("^[a-zA-Z-]*$", var.function_name))
    error_message = "The function name should only contain characters or hyphens (-)."
  }
}

variable "s3_source_bucket" {
  type        = string
  description = "Bucket to upload the source code to/fetch the source code from"
}

variable "source_dir" {
  type        = string
  description = "Local path to find the lambda script(s) in"
}
variable "execution_role_policies" {
  type = list(
    object({
      name = string
      json = string
    })
  )

  description = "Additional policies to attach to the execution role"
  default     = []
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}

// -- Optional variables --------------------------------------------------------------------

variable "layers" {
  type        = list(string)
  description = "Layers (arns) that should be attached to the lambda"
  default     = []
}

variable "function_handler" {
  type        = string
  description = "Name of the function to call"
  default     = "index.lambda_handler"
}

variable "function_runtime" {
  type        = string
  description = "Lambda runtime environment"
  default     = "python3.8"
}

variable "function_timeout" {
  type        = number
  description = "Max runtime of the lambda function in s"
  default     = 720
}

variable "environment" {
  type        = map(string)
  description = "List of environment variables in key-value format"
  default = {
    "MODULE" = "Generic Lambda Moduel"
  }
}

variable "vpc" {
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  description = "Lambda will be deployed in VPC when this variable is set and not null"
  default     = null
}

