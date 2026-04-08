"""
Flask application factory for CloudTask Manager.
Configures the application and registers route blueprints.
"""
import os
from flask import Flask


def create_app():
    """
    Create and configure the Flask application instance.

    Returns:
        Flask: Configured Flask application.
    """
    app = Flask(__name__)

    # Application configuration loaded from environment variables
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cloudtask-secret-key-2024")
    app.config["AWS_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")
    app.config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    app.config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    app.config["S3_BUCKET"] = os.environ.get("S3_BUCKET", "cloudtask-attachments-614939596951")
    app.config["DYNAMODB_TABLE"] = os.environ.get("DYNAMODB_TABLE", "CloudTasks")
    app.config["SNS_TOPIC_ARN"] = os.environ.get("SNS_TOPIC_ARN", "")
    app.config["LAMBDA_FUNCTION_NAME"] = os.environ.get("LAMBDA_FUNCTION_NAME", "cloud-task-processor")
    app.config["CLOUDWATCH_LOG_GROUP"] = os.environ.get("CLOUDWATCH_LOG_GROUP", "/cloudtask/application")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload size

    # Register the task routes blueprint
    from app.routes.task_routes import task_bp
    app.register_blueprint(task_bp)

    return app
