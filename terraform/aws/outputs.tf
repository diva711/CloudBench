output "s3_bucket_name" {
  description = "Name of the S3 bucket for results"
  value       = aws_s3_bucket.benchmark_results.bucket
}

output "ec2_public_ip" {
  description = "Public IP of the benchmark VM"
  value       = aws_instance.benchmark_vm.public_ip
}