variable "aws_region" {
  default = "ap-south-1"
}

variable "ami_id" {
  description = "Amazon Linux 2 AMI for ap-south-1"
  default     = "ami-0f58b397bc5c1f2e8"
}

variable "instance_type" {
  default = "t2.micro"
}

variable "db_username" {
  default = "benchmarkadmin"
}

variable "db_password" {
  sensitive = true
  default   = "BenchmarkPass2024!"
}