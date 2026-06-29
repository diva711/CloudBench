terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_key_pair" "cloudbench_key" {
  key_name = "cloudbench-key"
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "benchmark_results" {
  bucket        = "cloudbench-results-${random_id.suffix.hex}"
  force_destroy = true

  tags = {
    Project = "CloudBench"
  }
}

resource "aws_security_group" "benchmark_sg" {
  name        = "cloudbench-sg"
  description = "Allow HTTP and SSH for benchmarking"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "benchmark_vm" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = data.aws_key_pair.cloudbench_key.key_name
  vpc_security_group_ids = [aws_security_group.benchmark_sg.id]

  tags = {
    Name    = "cloudbench-vm"
    Project = "CloudBench"
  }
}

resource "aws_db_instance" "benchmark_db" {
  identifier          = "cloudbench-db"
  engine              = "postgres"
  engine_version      = "15"
  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  db_name             = "benchmarkdb"
  username            = "benchmarkadmin"
  password            = "BenchmarkPass2024!"
  skip_final_snapshot = true
  publicly_accessible = true
  tags = { Project = "CloudBench" }
}

output "rds_endpoint" {
  value = aws_db_instance.benchmark_db.endpoint
}