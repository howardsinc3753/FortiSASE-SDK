terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  # For SSO/named-profile accounts (e.g. the corp SE lab), either set
  # AWS_PROFILE in the environment, or uncomment the next line:
  # profile = var.aws_profile
}
