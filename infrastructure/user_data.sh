#!/bin/bash
# ------------------------------------------------------------------
# CloudTask Manager - EC2 Instance Bootstrap Script
# This script runs once when the EC2 instance is first launched.
# It installs dependencies, clones the application, and configures
# a systemd service for automatic application management.
# ------------------------------------------------------------------

set -e

# Update system packages
yum update -y

# Install Python 3, pip, and git
yum install -y python3 python3-pip git

# Clone the application repository from GitHub
cd /home/ec2-user
git clone https://${github_pat}@github.com/PiyushWagh18/ccp.git app
cd app

# Install Python dependencies
pip3 install -r requirements.txt

# Install the custom cloudlib library in editable mode
pip3 install -e .

# Create environment configuration file for the application
# Note: AWS credentials are NOT included here; the EC2 IAM role provides them
cat > /home/ec2-user/app/.env << EOF
AWS_REGION=${aws_region}
S3_BUCKET=${s3_bucket}
DYNAMODB_TABLE=${dynamodb_table}
SNS_TOPIC_ARN=${sns_topic_arn}
LAMBDA_FUNCTION_NAME=${lambda_function_name}
CLOUDWATCH_LOG_GROUP=${cloudwatch_log_group}
FLASK_DEBUG=False
PORT=80
SECRET_KEY=cloudtask-production-secret-$(date +%s)
EOF

# Set correct ownership
chown -R ec2-user:ec2-user /home/ec2-user/app

# Create a systemd service for automatic application management
cat > /etc/systemd/system/cloudtask.service << 'SERVICEEOF'
[Unit]
Description=CloudTask Manager Application
After=network.target

[Service]
User=root
WorkingDirectory=/home/ec2-user/app
EnvironmentFile=/home/ec2-user/app/.env
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:80 --workers 2 --timeout 120 "app:create_app()"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd, enable and start the CloudTask service
systemctl daemon-reload
systemctl enable cloudtask
systemctl start cloudtask
