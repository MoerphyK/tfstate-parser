variable "tfe_endpoint" {
  type        = string
  description = "Terraform Cloud or Enterprise API endpoint"
  default     = "https://app.terraform.io/api/v2"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}