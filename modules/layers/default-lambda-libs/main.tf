terraform {
  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "2.3.0"
    }
  }
}

data "archive_file" "zip_file" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/build/package.zip"
  # This hopefully fixes TFE from detecting changes everytime we plan
  output_file_mode = "0666"
}

resource "aws_s3_object" "object" {
  bucket = var.s3_source_bucket
  key    = "src/layer/default/package-${data.archive_file.zip_file.output_md5}.zip"
  source = "${path.module}/build/package.zip"
  etag   = data.archive_file.zip_file.output_md5
  tags   = var.tags

  lifecycle {
    ignore_changes = [
      # Ignore changes to etag since tf change detection conflicts with kms encryption
      etag,
    ]
  }
}

resource "aws_lambda_layer_version" "lambda_layer" {
  compatible_architectures = ["x86_64"]
  s3_bucket                = var.s3_source_bucket
  s3_key                   = aws_s3_object.object.id
  s3_object_version        = aws_s3_object.object.version_id
  description              = "Default libraries for TFState parser lambdas"
  layer_name               = "${var.resource_prefix}-${var.lambda_layer_name}"
  compatible_runtimes      = [var.function_runtime]
}