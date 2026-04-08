# ------------------------------------------------------------------
# CloudTask Manager - Terraform Variable Definitions
# ------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-north-1"
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance (Amazon Linux 2023)"
  type        = string
  default     = "ami-077d1b9f9a1902bbc"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
  default     = "cloud-key-pair"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for storing tasks"
  type        = string
  default     = "CloudTasks"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for file attachments (must be globally unique)"
  type        = string
  default     = "cloudtask-attachments-614939596951"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function for task processing"
  type        = string
  default     = "cloud-task-processor"
}

variable "notification_email" {
  description = "Email address for SNS task notifications (leave empty to skip)"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/PiyushWagh18/ccp"
}

variable "github_pat" {
  description = "GitHub Personal Access Token for cloning private repo"
  type        = string
  sensitive   = true
}
