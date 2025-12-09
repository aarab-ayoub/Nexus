terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  access_key = "minioadmin"
  secret_key = "minioadmin"
  region     = "us-east-1"

  # Make the AWS provider talk to a local MinIO server (S3-compatible)
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true

  # Avoid requesting AWS account details when using an S3-compatible server like MinIO
  skip_requesting_account_id = true

  endpoints {
    s3 = "http://localhost:9000"
  }
}

resource "aws_s3_bucket" "raw-data-bucket" {
  bucket = "raw-data"
  acl    = "private"
}