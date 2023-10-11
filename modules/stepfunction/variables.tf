variable "sfn_name" {
  type    = string
  default = "compliance-checker"
  description = "name of the step function"
}

variable "functions" {
  type        = map(string)
  description = "List of ARNs of the lambda functions called in the SFN. Key should be the template variable name, value the lambda arn"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}