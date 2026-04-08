"""
Lambda service for CloudTask Manager.
Wraps cloudlib.CloudComputeManager with application-specific task processing logic.
"""
import os
from app.services import get_cloud_manager


class TaskProcessorService:
    """
    Application service layer for Lambda-based task processing.
    Uses the cloudlib CloudComputeManager to invoke the
    cloud-task-processor Lambda function asynchronously for
    background processing of newly created tasks.
    """

    def __init__(self):
        """Initialise with shared CloudManager and Lambda function name from config."""
        cloud = get_cloud_manager()
        self.compute = cloud.compute
        self.function_name = os.environ.get("LAMBDA_FUNCTION_NAME", "cloud-task-processor")

    def process_task(self, task_data):
        """
        Invoke the Lambda function asynchronously to process a task.
        The Lambda function computes metadata such as word count
        and updates the task record in DynamoDB.

        Args:
            task_data (dict): Task data to process.

        Returns:
            dict: Invocation result with 'success' and 'status_code'.
        """
        payload = {
            "task_id": task_data.get("task_id"),
            "title": task_data.get("title"),
            "description": task_data.get("description", ""),
            "action": "process_new_task",
        }
        return self.compute.invoke_async(self.function_name, payload)

    def get_processor_status(self):
        """
        Check the status of the task processor Lambda function.

        Returns:
            dict: Function configuration details or None if unavailable.
        """
        return self.compute.get_function_info(self.function_name)
