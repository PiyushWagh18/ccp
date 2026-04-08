# ------------------------------------------------------------------
# CloudTask Manager - Terraform Infrastructure Configuration
# Provisions all required AWS resources for the application:
# EC2, DynamoDB, S3, SNS, Lambda, CloudWatch, IAM
# ------------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.0"
}

# AWS provider configuration using variables for credentials
provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}

# ============================================================
# DATA SOURCES
# ============================================================

# Use the default VPC for simplicity
data "aws_vpc" "default" {
  default = true
}

# Get default subnets in the VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ============================================================
# SECURITY GROUP - EC2
# ============================================================

resource "aws_security_group" "cloudtask_sg" {
  name        = "cloudtask-sg"
  description = "Security group for CloudTask Manager - allows HTTP, HTTPS and SSH"
  vpc_id      = data.aws_vpc.default.id

  # Allow HTTP traffic on port 80
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH access for deployment
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow Flask dev server port
  ingress {
    description = "Flask Dev Server"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "cloudtask-sg"
    Project = "CloudTask Manager"
  }
}

# ============================================================
# IAM - EC2 ROLE AND INSTANCE PROFILE
# ============================================================

resource "aws_iam_role" "ec2_role" {
  name = "cloudtask-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "cloudtask-ec2-role"
    Project = "CloudTask Manager"
  }
}

# Policy granting EC2 access to DynamoDB, S3, SNS, Lambda, CloudWatch
resource "aws_iam_role_policy" "ec2_policy" {
  name = "cloudtask-ec2-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Scan",
          "dynamodb:Query",
          "dynamodb:DescribeTable"
        ]
        Resource = aws_dynamodb_table.cloudtasks.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.attachments.arn,
          "${aws_s3_bucket.attachments.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:ListTopics",
          "sns:ListSubscriptionsByTopic"
        ]
        Resource = aws_sns_topic.task_notifications.arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
          "lambda:GetFunction",
          "lambda:ListFunctions"
        ]
        Resource = aws_lambda_function.task_processor.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams",
          "logs:DescribeLogGroups",
          "logs:GetLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.app_logs.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "cloudtask-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# ============================================================
# DYNAMODB TABLE
# ============================================================

resource "aws_dynamodb_table" "cloudtasks" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "task_id"

  attribute {
    name = "task_id"
    type = "S"
  }

  tags = {
    Name    = "CloudTasks"
    Project = "CloudTask Manager"
  }
}

# ============================================================
# S3 BUCKET
# ============================================================

resource "aws_s3_bucket" "attachments" {
  bucket = var.s3_bucket_name

  tags = {
    Name    = "cloudtask-attachments"
    Project = "CloudTask Manager"
  }
}

# Block all public access to the attachment bucket
resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable server-side encryption for the bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ============================================================
# SNS TOPIC
# ============================================================

resource "aws_sns_topic" "task_notifications" {
  name = "CloudTaskNotifications"

  tags = {
    Name    = "CloudTaskNotifications"
    Project = "CloudTask Manager"
  }
}

# Optional email subscription (requires manual confirmation)
resource "aws_sns_topic_subscription" "email" {
  count     = var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.task_notifications.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# ============================================================
# CLOUDWATCH LOG GROUP
# ============================================================

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/cloudtask/application"
  retention_in_days = 14

  tags = {
    Name    = "cloudtask-logs"
    Project = "CloudTask Manager"
  }
}

# ============================================================
# IAM - LAMBDA EXECUTION ROLE
# ============================================================

resource "aws_iam_role" "lambda_role" {
  name = "cloudtask-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "cloudtask-lambda-role"
    Project = "CloudTask Manager"
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "cloudtask-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.cloudtasks.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.task_notifications.arn
      }
    ]
  })
}

# ============================================================
# LAMBDA FUNCTION
# ============================================================

# Package the Lambda function source code into a ZIP
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/task_processor.py"
  output_path = "${path.module}/../lambda/task_processor.zip"
}

resource "aws_lambda_function" "task_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "task_processor.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      SNS_TOPIC_ARN  = aws_sns_topic.task_notifications.arn
    }
  }

  tags = {
    Name    = "cloud-task-processor"
    Project = "CloudTask Manager"
  }
}

# ============================================================
# EC2 INSTANCE
# ============================================================

resource "aws_instance" "cloudtask_server" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  vpc_security_group_ids = [aws_security_group.cloudtask_sg.id]

  # Bootstrap the instance with the application
  user_data = templatefile("${path.module}/user_data.sh", {
    github_repo          = var.github_repo
    github_pat           = var.github_pat
    aws_region           = var.aws_region
    s3_bucket            = var.s3_bucket_name
    dynamodb_table       = var.dynamodb_table_name
    sns_topic_arn        = aws_sns_topic.task_notifications.arn
    lambda_function_name = var.lambda_function_name
    cloudwatch_log_group = "/cloudtask/application"
  })

  tags = {
    Name    = "CloudTask-Server"
    Project = "CloudTask Manager"
  }
}
