variable "functions" {
  type        = map(string)
  description = "ARNs of the lambda functions called in the SFN. Key should be the template variable name, value the lambda arn"
}

variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}