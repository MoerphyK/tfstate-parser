variable "encryption_key_id" {
  type = string
  description = "The KMS key ID used to encrypt the S3 buckets"
}

variable "resource_prefix" {
  type = string
  description = "prefix for all resources created by this module"
}

variable "tags" {
  type = map(string)
  description = "tags to apply to all resources created by this module"
}