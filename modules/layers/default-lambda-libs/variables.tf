variable "s3_source_bucket" {
  type = string
}

variable "lambda_layer_name" {
  type    = string
  default = "default-libs"
}

variable "function_runtime" {
  type    = string
  default = "python3.8"
}

variable "resource_prefix" {
  type = string
}

variable "tags" {
  type = map(string)
}