"""
CloudComputeManager - Manages AWS Lambda serverless compute operations.

Provides methods for invoking Lambda functions, checking function
status, and managing serverless compute tasks.
"""
import json
from botocore.exceptions import ClientError


class CloudComputeManager:
    """
    Object-oriented interface for AWS Lambda operations.
    Supports synchronous and asynchronous function invocation,
    function status checks, and response handling.

    Attributes:
        lambda_client: boto3 Lambda client.
        region (str): AWS region name.
    """

    def __init__(self, session, region):
        """
        Initialize CloudComputeManager with an AWS session.

        Args:
            session (boto3.Session): Active boto3 session.
            region (str): AWS region name.
        """
        self.lambda_client = session.client("lambda", region_name=region)
        self.region = region

    def invoke_function(self, function_name, payload, invocation_type="Event"):
        """
        Invoke a Lambda function with the given payload.

        Args:
            function_name (str): Name or ARN of the Lambda function.
            payload (dict): Input data to pass to the Lambda function.
            invocation_type (str): 'RequestResponse' for synchronous,
                                   'Event' for asynchronous invocation.
                                   Default is 'Event' (async).

        Returns:
            dict: Result with 'success', 'status_code', and optionally 'response'.
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload),
            )

            result = {
                "success": True,
                "status_code": response["StatusCode"],
            }

            # For synchronous invocations, parse the response payload
            if invocation_type == "RequestResponse":
                response_payload = response["Payload"].read().decode("utf-8")
                result["response"] = json.loads(response_payload)

            return result
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def invoke_sync(self, function_name, payload):
        """
        Invoke a Lambda function synchronously and wait for the response.

        Args:
            function_name (str): Lambda function name.
            payload (dict): Input data for the function.

        Returns:
            dict: Result with 'success', 'status_code', and 'response'.
        """
        return self.invoke_function(function_name, payload, invocation_type="RequestResponse")

    def invoke_async(self, function_name, payload):
        """
        Invoke a Lambda function asynchronously (fire and forget).

        Args:
            function_name (str): Lambda function name.
            payload (dict): Input data for the function.

        Returns:
            dict: Result with 'success' and 'status_code'.
        """
        return self.invoke_function(function_name, payload, invocation_type="Event")

    def get_function_info(self, function_name):
        """
        Retrieve configuration details of a Lambda function.

        Args:
            function_name (str): Lambda function name.

        Returns:
            dict: Function configuration or None on error.
        """
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response.get("Configuration")
        except ClientError:
            return None

    def list_functions(self):
        """
        List all Lambda functions in the current region.

        Returns:
            list: List of function configuration dictionaries.
        """
        try:
            response = self.lambda_client.list_functions()
            return response.get("Functions", [])
        except ClientError:
            return []

    def health_check(self):
        """
        Verify Lambda service connectivity.

        Returns:
            bool: True if Lambda is accessible, False otherwise.
        """
        try:
            self.lambda_client.list_functions(MaxItems=1)
            return True
        except ClientError:
            return False
