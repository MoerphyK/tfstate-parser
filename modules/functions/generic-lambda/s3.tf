# Zip the Lambda source code
data "archive_file" "zip_file" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = local.tmp_build_path
  # This hopefully fixes TFE from detecting changes everytime we plan
  output_file_mode = "0666"
}

# Upload the zip file to S3
resource "aws_s3_object" "object" {
  bucket = var.s3_source_bucket
  key    = "src/${var.function_name}/${var.function_name}-${data.archive_file.zip_file.output_md5}.zip"
  source = local.tmp_build_path
  etag   = data.archive_file.zip_file.output_md5
  tags   = var.tags

  lifecycle {
    ignore_changes = [
      # Ignore changes to etag since tf change detection conflicts with kms encryption
      etag,
    ]
  }
}