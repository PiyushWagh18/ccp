# ------------------------------------------------------------------
# CloudTask Manager - Terraform Outputs
# ------------------------------------------------------------------

output "ec2_public_ip" {
  description = "Public IP address of the CloudTask Manager EC2 instance"
  value       = aws_instance.cloudtask_server.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.cloudtask_server.public_dns
}

output "application_url" {
  description = "URL to access the deployed CloudTask Manager application"
  value       = "http://${aws_instance.cloudtask_server.public_ip}"
}

output "dynamodb_table" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.cloudtasks.name
}

output "s3_bucket" {
  description = "Name of the S3 bucket for attachments"
  value       = aws_s3_bucket.attachments.bucket
}

output "sns_topic_arn" {
  description = "ARN of the SNS notification topic"
  value       = aws_sns_topic.task_notifications.arn
}

output "lambda_function" {
  description = "Name of the Lambda task processor function"
  value       = aws_lambda_function.task_processor.function_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for the application"
  value       = aws_cloudwatch_log_group.app_logs.name
}
