"""
CloudLogger - Manages AWS CloudWatch Logs operations.

Provides methods for creating log groups, log streams, and
writing log events to Amazon CloudWatch for application monitoring.
"""
import time
from datetime import datetime
from botocore.exceptions import ClientError


class CloudLogger:
    """
    Object-oriented interface for AWS CloudWatch Logs.
    Supports log group and stream management, writing log events,
    and retrieving recent log entries for monitoring purposes.

    Attributes:
        logs_client: boto3 CloudWatch Logs client.
        cloudwatch_client: boto3 CloudWatch client for metrics.
        region (str): AWS region name.
    """

    def __init__(self, session, region):
        """
        Initialize CloudLogger with an AWS session.

        Args:
            session (boto3.Session): Active boto3 session.
            region (str): AWS region name.
        """
        self.logs_client = session.client("logs", region_name=region)
        self.cloudwatch_client = session.client("cloudwatch", region_name=region)
        self.region = region

    def create_log_group(self, log_group_name):
        """
        Create a CloudWatch log group (idempotent).

        Args:
            log_group_name (str): Name of the log group to create.

        Returns:
            dict: Result with 'success' boolean.
        """
        try:
            self.logs_client.create_log_group(logGroupName=log_group_name)
            return {"success": True, "log_group": log_group_name}
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            # Log group already exists, which is acceptable
            return {"success": True, "log_group": log_group_name}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def create_log_stream(self, log_group_name, log_stream_name):
        """
        Create a log stream within an existing log group.

        Args:
            log_group_name (str): Parent log group name.
            log_stream_name (str): Name of the log stream to create.

        Returns:
            dict: Result with 'success' boolean.
        """
        try:
            self.logs_client.create_log_stream(
                logGroupName=log_group_name, logStreamName=log_stream_name
            )
            return {"success": True, "log_stream": log_stream_name}
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            return {"success": True, "log_stream": log_stream_name}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def put_log_event(self, log_group_name, log_stream_name, message):
        """
        Write a single log event to a CloudWatch log stream.

        Args:
            log_group_name (str): Target log group name.
            log_stream_name (str): Target log stream name.
            message (str): Log message content.

        Returns:
            dict: Result with 'success' and 'sequence_token'.
        """
        try:
            # Get the current sequence token for the log stream
            response = self.logs_client.describe_log_streams(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_name,
                limit=1,
            )
            streams = response.get("logStreams", [])

            put_kwargs = {
                "logGroupName": log_group_name,
                "logStreamName": log_stream_name,
                "logEvents": [
                    {"timestamp": int(time.time() * 1000), "message": message}
                ],
            }

            # Include sequence token if the stream already has events
            if streams and "uploadSequenceToken" in streams[0]:
                put_kwargs["sequenceToken"] = streams[0]["uploadSequenceToken"]

            response = self.logs_client.put_log_events(**put_kwargs)
            return {"success": True, "sequence_token": response.get("nextSequenceToken")}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def get_recent_logs(self, log_group_name, log_stream_name, limit=50):
        """
        Retrieve recent log events from a CloudWatch log stream.

        Args:
            log_group_name (str): Log group name.
            log_stream_name (str): Log stream name.
            limit (int): Maximum number of events to return. Default 50.

        Returns:
            list: List of log event dictionaries with 'timestamp' and 'message'.
        """
        try:
            response = self.logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=log_stream_name,
                limit=limit,
                startFromHead=False,
            )
            return response.get("events", [])
        except ClientError:
            return []

    def put_metric(self, namespace, metric_name, value, unit="Count"):
        """
        Publish a custom metric to CloudWatch.

        Args:
            namespace (str): CloudWatch metric namespace.
            metric_name (str): Name of the metric.
            value (float): Metric value.
            unit (str): Metric unit (Count, Seconds, Bytes, etc.).

        Returns:
            dict: Result with 'success' boolean.
        """
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Timestamp": datetime.utcnow(),
                    }
                ],
            )
            return {"success": True}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def health_check(self):
        """
        Verify CloudWatch Logs service connectivity.

        Returns:
            bool: True if CloudWatch Logs is accessible, False otherwise.
        """
        try:
            self.logs_client.describe_log_groups(limit=1)
            return True
        except ClientError:
            return False
