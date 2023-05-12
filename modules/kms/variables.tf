variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}

variable "external_roles_lisa_bucket" {
  type        = list(string)
  description = "IAM roles & users for Lisa S3 bucket access"
}