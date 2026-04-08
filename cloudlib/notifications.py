"""
CloudNotificationManager - Manages AWS SNS notification operations.

Provides methods for creating topics, managing subscriptions,
and publishing messages through Amazon Simple Notification Service.
"""
from botocore.exceptions import ClientError


class CloudNotificationManager:
    """
    Object-oriented interface for AWS SNS operations.
    Supports topic creation, subscription management, and
    message publishing for application notifications.

    Attributes:
        sns_client: boto3 SNS client.
        region (str): AWS region name.
    """

    def __init__(self, session, region):
        """
        Initialize CloudNotificationManager with an AWS session.

        Args:
            session (boto3.Session): Active boto3 session.
            region (str): AWS region name.
        """
        self.sns_client = session.client("sns", region_name=region)
        self.region = region

    def create_topic(self, topic_name):
        """
        Create an SNS topic (idempotent - returns existing topic ARN if it exists).

        Args:
            topic_name (str): Name for the SNS topic.

        Returns:
            dict: Result with 'success' and 'topic_arn', or 'error'.
        """
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            return {"success": True, "topic_arn": response["TopicArn"]}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def subscribe(self, topic_arn, protocol, endpoint):
        """
        Subscribe an endpoint to an SNS topic.

        Args:
            topic_arn (str): ARN of the SNS topic.
            protocol (str): Subscription protocol ('email', 'sms', 'https', 'lambda').
            endpoint (str): Endpoint address (email, phone number, URL, Lambda ARN).

        Returns:
            dict: Result with 'success' and 'subscription_arn'.
        """
        try:
            response = self.sns_client.subscribe(
                TopicArn=topic_arn, Protocol=protocol, Endpoint=endpoint
            )
            return {"success": True, "subscription_arn": response["SubscriptionArn"]}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def publish_message(self, topic_arn, subject, message):
        """
        Publish a message to an SNS topic, delivering to all subscribers.

        Args:
            topic_arn (str): ARN of the target SNS topic.
            subject (str): Message subject line (used for email subscriptions).
            message (str): Message body content.

        Returns:
            dict: Result with 'success' and 'message_id'.
        """
        try:
            response = self.sns_client.publish(
                TopicArn=topic_arn, Subject=subject, Message=message
            )
            return {"success": True, "message_id": response["MessageId"]}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def list_topics(self):
        """
        List all SNS topics in the current region.

        Returns:
            list: List of topic ARN strings.
        """
        try:
            response = self.sns_client.list_topics()
            return [t["TopicArn"] for t in response.get("Topics", [])]
        except ClientError:
            return []

    def list_subscriptions(self, topic_arn):
        """
        List all subscriptions for a specific SNS topic.

        Args:
            topic_arn (str): ARN of the SNS topic.

        Returns:
            list: List of subscription dictionaries.
        """
        try:
            response = self.sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
            return response.get("Subscriptions", [])
        except ClientError:
            return []

    def health_check(self):
        """
        Verify SNS service connectivity.

        Returns:
            bool: True if SNS is accessible, False otherwise.
        """
        try:
            self.sns_client.list_topics()
            return True
        except ClientError:
            return False
