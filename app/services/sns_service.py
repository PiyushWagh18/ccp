"""
SNS service for CloudTask Manager.
Wraps cloudlib.CloudNotificationManager with application-specific notification logic.
"""
import os
from app.services import get_cloud_manager


class TaskNotificationService:
    """
    Application service layer for SNS task notifications.
    Uses the cloudlib CloudNotificationManager to publish
    notification messages when tasks are created, updated, or deleted.
    """

    def __init__(self):
        """Initialise with shared CloudManager and SNS topic ARN from config."""
        cloud = get_cloud_manager()
        self.notifications = cloud.notifications
        self.topic_arn = os.environ.get("SNS_TOPIC_ARN", "")

    def notify_task_created(self, task_data):
        """
        Send a notification when a new task is created.

        Args:
            task_data (dict): The created task data.

        Returns:
            dict: Publish result or None if topic not configured.
        """
        if not self.topic_arn:
            return None
        subject = f"New Task Created: {task_data.get('title', 'Untitled')}"
        message = (
            f"A new task has been created in CloudTask Manager.\n\n"
            f"Title: {task_data.get('title')}\n"
            f"Description: {task_data.get('description', 'N/A')}\n"
            f"Priority: {task_data.get('priority', 'medium')}\n"
            f"Status: {task_data.get('status', 'pending')}\n"
            f"Created At: {task_data.get('created_at')}\n"
            f"Task ID: {task_data.get('task_id')}"
        )
        return self.notifications.publish_message(self.topic_arn, subject, message)

    def notify_task_updated(self, task_id, title):
        """
        Send a notification when a task is updated.

        Args:
            task_id (str): ID of the updated task.
            title (str): Updated task title.

        Returns:
            dict: Publish result or None if topic not configured.
        """
        if not self.topic_arn:
            return None
        subject = f"Task Updated: {title}"
        message = (
            f"A task has been updated in CloudTask Manager.\n\n"
            f"Title: {title}\n"
            f"Task ID: {task_id}"
        )
        return self.notifications.publish_message(self.topic_arn, subject, message)

    def notify_task_deleted(self, title):
        """
        Send a notification when a task is deleted.

        Args:
            title (str): Title of the deleted task.

        Returns:
            dict: Publish result or None if topic not configured.
        """
        if not self.topic_arn:
            return None
        subject = f"Task Deleted: {title}"
        message = (
            f"A task has been deleted from CloudTask Manager.\n\n"
            f"Title: {title}"
        )
        return self.notifications.publish_message(self.topic_arn, subject, message)
