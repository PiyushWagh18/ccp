"""
DynamoDB service for CloudTask Manager.
Wraps cloudlib.CloudDatabaseManager with application-specific task operations.
"""
import os
from app.services import get_cloud_manager


class TaskDatabaseService:
    """
    Application service layer for DynamoDB task operations.
    Uses the cloudlib CloudDatabaseManager to perform CRUD operations
    on the CloudTasks DynamoDB table.
    """

    def __init__(self):
        """Initialise with shared CloudManager and table name from config."""
        cloud = get_cloud_manager()
        self.db = cloud.database
        self.table_name = os.environ.get("DYNAMODB_TABLE", "CloudTasks")

    def create_task(self, task_data):
        """
        Create a new task in DynamoDB.

        Args:
            task_data (dict): Task attributes including task_id, title, description, etc.

        Returns:
            dict: Result with 'success' boolean.
        """
        return self.db.put_item(self.table_name, task_data)

    def get_task(self, task_id):
        """
        Retrieve a single task by its ID.

        Args:
            task_id (str): Unique task identifier.

        Returns:
            dict: Task item or None if not found.
        """
        return self.db.get_item(self.table_name, {"task_id": task_id})

    def get_all_tasks(self):
        """
        Retrieve all tasks from the DynamoDB table.

        Returns:
            list: List of task dictionaries.
        """
        return self.db.scan_table(self.table_name)

    def update_task(self, task_id, update_data):
        """
        Update specific attributes of a task.

        Args:
            task_id (str): Task to update.
            update_data (dict): Key-value pairs of attributes to update.

        Returns:
            dict: Result with 'success' and updated attributes.
        """
        return self.db.update_item(
            self.table_name, {"task_id": task_id}, update_data
        )

    def delete_task(self, task_id):
        """
        Delete a task from DynamoDB.

        Args:
            task_id (str): Task to delete.

        Returns:
            dict: Result with 'success' boolean.
        """
        return self.db.delete_item(self.table_name, {"task_id": task_id})
