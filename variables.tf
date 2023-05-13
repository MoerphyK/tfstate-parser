variable "tfe_endpoint" {
  type        = string
  description = "endpoint for the post /create /update tfe CMDB CI VM instance"
  default = "https://app.terraform.io/api/v2"
}

variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}