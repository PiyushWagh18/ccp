CloudTask Manager - Cloud-Based Task Management Application
============================================================

A dynamic cloud-based task management application built with Python Flask,
deployed on AWS using five cloud services: DynamoDB, S3, SNS, Lambda, and CloudWatch.
Includes a custom OOP library (piyush-cloudlib) for AWS service abstractions.

DEPENDENCIES
------------
- Python 3.10+
- Flask 3.0+
- boto3 1.34+
- python-dotenv 1.0+
- gunicorn 21.2+
- pytest 7.4+
- Terraform 1.0+ (for infrastructure provisioning)
- AWS CLI (configured with valid credentials)

INSTALLATION
------------
1. Clone the repository:
   git clone https://github.com/PiyushWagh18/ccp.git
   cd ccp

2. Create and activate virtual environment:
   python -m venv venv
   source venv/bin/activate  (Linux/Mac)
   venv\Scripts\activate     (Windows)

3. Install dependencies:
   pip install -r requirements.txt

4. Install the custom cloud library:
   pip install -e .

5. Configure environment variables:
   Copy .env.example to .env and fill in your AWS credentials and configuration.

CONFIGURATION FILES
-------------------
- .env                          : Environment variables (AWS credentials, service names)
- infrastructure/variables.tf   : Terraform variable definitions
- infrastructure/main.tf        : AWS infrastructure definitions
- .github/workflows/deploy.yml  : CI/CD pipeline configuration

DEPLOYMENT STEPS
----------------
1. Provision AWS Infrastructure:
   cd infrastructure
   terraform init
   terraform plan
   terraform apply

2. Note the EC2 public IP from Terraform output.

3. Configure GitHub Secrets:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - EC2_HOST (EC2 public IP)
   - EC2_SSH_KEY (contents of cloud-key-pair.pem)

4. Push code to GitHub main branch to trigger CI/CD deployment.

5. Access the application at: http://<EC2_PUBLIC_IP>

LOCAL DEVELOPMENT
-----------------
1. Ensure .env file is configured with valid AWS credentials.
2. Run the application:
   python run.py
3. Access at http://localhost:5000

RUNNING TESTS
-------------
   pytest tests/ -v

AWS CLOUD SERVICES USED
------------------------
1. Amazon DynamoDB  - NoSQL database for task data persistence
2. Amazon S3        - Object storage for file attachments
3. Amazon SNS       - Notification service for task event alerts
4. AWS Lambda       - Serverless compute for background task processing
5. Amazon CloudWatch - Application logging and monitoring

CUSTOM LIBRARY
--------------
piyush-cloudlib provides OOP abstractions over AWS services:
- CloudManager       : Facade orchestrator for all cloud services
- CloudStorageManager    : S3 file operations (upload, download, delete)
- CloudDatabaseManager   : DynamoDB CRUD operations
- CloudNotificationManager : SNS topic and message management
- CloudLogger            : CloudWatch logging
- CloudComputeManager    : Lambda function invocation

PROJECT STRUCTURE
-----------------
ccp/
  app/                    : Flask application
    routes/               : HTTP route handlers (CRUD operations)
    services/             : Service layer (uses cloudlib)
    templates/            : Jinja2 HTML templates
    static/               : CSS and JavaScript files
  cloudlib/               : Custom OOP cloud library
  infrastructure/         : Terraform IaC files
  lambda/                 : AWS Lambda function code
  tests/                  : Unit tests
  .github/workflows/      : GitHub Actions CI/CD pipeline
  run.py                  : Application entry point
  setup.py                : Library package setup
  requirements.txt        : Python dependencies
