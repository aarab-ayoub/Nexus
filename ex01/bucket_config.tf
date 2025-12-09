provider "aws" {
  region = "us-east-1"

  access_key = "minioadmin"
  secret_key = "minioadmin"
  endpoint = "http://localhost:9000"
  s3_force_path_style = true # Required for MinIO
}

resource "aws_s3_bucket" "raw-data-bucket" {
	bucker = "raw-data"
}