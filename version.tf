terraform {
  cloud {
    organization = "AXA-GroupOperations"

    workspaces {
      name = "SP-Compliance-Checker"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0.0"
    }
  }

}

provider "aws" {
  region = "eu-central-1"
}