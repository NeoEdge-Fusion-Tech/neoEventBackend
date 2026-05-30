terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # For production, you should use an S3 backend for state
  # backend "s3" {
  #   bucket = "neoevents-terraform-state"
  #   key    = "prod/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "prod"
}

variable "db_password" {
  description = "Password for the RDS database"
  type        = string
  sensitive   = true
}
