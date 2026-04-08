"""
CloudWatch service for CloudTask Manager.
Wraps cloudlib.CloudLogger with application-specific logging and monitoring.
"""
import os
from datetime import datetime
from app.services import get_cloud_manager


class AppMonitoringService:
    """
    Application service layer for CloudWatch logging and monitoring.
    Uses the cloudlib CloudLogger to write application events to
    CloudWatch Logs and publish custom metrics for task operations.
    """

    def __init__(self):
        """Initialise with shared CloudManager and log group from config."""
        cloud = get_cloud_manager()
        self.logger = cloud.logger
        self.log_group = os.environ.get("CLOUDWATCH_LOG_GROUP", "/cloudtask/application")
        self.log_stream = f"app-{datetime.utcnow().strftime('%Y-%m-%d')}"

        # Ensure the log group and daily log stream exist
        self.logger.create_log_group(self.log_group)
        self.logger.create_log_stream(self.log_group, self.log_stream)

    def log_event(self, message):
        """
        Log an application event to CloudWatch Logs.

        Args:
            message (str): Event message to log.

        Returns:
            dict: Result with 'success' boolean.
        """
        timestamp = datetime.utcnow().isoformat()
        formatted_message = f"[{timestamp}] {message}"
        return self.logger.put_log_event(self.log_group, self.log_stream, formatted_message)

    def record_task_metric(self, metric_name, value=1):
        """
        Publish a custom task-related metric to CloudWatch.

        Args:
            metric_name (str): Name of the metric (e.g., 'TasksCreated').
            value (float): Metric value. Default 1.

        Returns:
            dict: Result with 'success' boolean.
        """
        return self.logger.put_metric("CloudTaskManager", metric_name, value)

    def get_recent_logs(self, limit=50):
        """
        Retrieve recent application log entries.

        Args:
            limit (int): Maximum number of log events to return.

        Returns:
            list: List of log event dictionaries.
        """
        return self.logger.get_recent_logs(self.log_group, self.log_stream, limit)
