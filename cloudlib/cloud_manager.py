"""
CloudManager - Central orchestrator for all AWS cloud service interactions.

Implements the Facade design pattern to provide a unified interface for
managing multiple AWS cloud services through a single entry point.
"""
import boto3


class CloudManager:
    """
    Central manager class that orchestrates all cloud service interactions.
    Uses the Facade pattern to simplify access to S3, DynamoDB, SNS,
    Lambda, and CloudWatch services through dedicated manager objects.

    Attributes:
        region (str): AWS region for all service clients.
        session (boto3.Session): Shared AWS session.
        storage (CloudStorageManager): S3 operations manager.
        database (CloudDatabaseManager): DynamoDB operations manager.
        notifications (CloudNotificationManager): SNS operations manager.
        logger (CloudLogger): CloudWatch Logs manager.
        compute (CloudComputeManager): Lambda operations manager.
    """

    def __init__(self, region, aws_access_key_id=None, aws_secret_access_key=None):
        """
        Initialize CloudManager with AWS credentials and region.

        Args:
            region (str): AWS region name (e.g., 'eu-north-1').
            aws_access_key_id (str, optional): AWS access key. If not provided,
                boto3 falls back to IAM role or environment credentials.
            aws_secret_access_key (str, optional): AWS secret key.
        """
        self.region = region

        # Build session kwargs, omitting credentials if not provided
        # so boto3 can fall back to IAM instance profile on EC2
        session_kwargs = {"region_name": region}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.session = boto3.Session(**session_kwargs)

        # Initialize each service manager with the shared session
        from cloudlib.storage import CloudStorageManager
        from cloudlib.database import CloudDatabaseManager
        from cloudlib.notifications import CloudNotificationManager
        from cloudlib.logger import CloudLogger
        from cloudlib.compute import CloudComputeManager

        self.storage = CloudStorageManager(self.session, region)
        self.database = CloudDatabaseManager(self.session, region)
        self.notifications = CloudNotificationManager(self.session, region)
        self.logger = CloudLogger(self.session, region)
        self.compute = CloudComputeManager(self.session, region)

    def get_service_status(self):
        """
        Check connectivity status for all managed cloud services.

        Returns:
            dict: Service names mapped to boolean availability status.
        """
        return {
            "storage": self.storage.health_check(),
            "database": self.database.health_check(),
            "notifications": self.notifications.health_check(),
            "logger": self.logger.health_check(),
            "compute": self.compute.health_check(),
        }

    def __repr__(self):
        return f"CloudManager(region='{self.region}')"
