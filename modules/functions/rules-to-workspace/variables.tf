variable "function_name" {
  type        = string
  description = "Name of the function. Will be used as prefix for all related resources. Should not contain white spaces"
  default     = "rules-to-workspace"
}

variable "s3_source_bucket" {
  type        = string
  description = "Bucket to upload the source code to/fetch the source code from"
}

variable "layers" {
  type        = list(string)
  description = "Layers (arns) that should be attached to the lambda"
}

variable "rules_bucket" {
  type        = string
  description = "Bucket where the rules are stored"
}

variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}