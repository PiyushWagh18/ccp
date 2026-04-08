"""
AWS Lambda Function: Task Processor
Triggered asynchronously when a new task is created in CloudTask Manager.
Computes metadata (word count, estimated complexity) and updates the task
record in DynamoDB. Logs processing results to CloudWatch.

Cloud Services Used:
    - DynamoDB: Reads and updates task records
    - SNS: Sends processing completion notification
    - CloudWatch Logs: Automatic Lambda logging
"""
import os
import json
import boto3
from datetime import datetime

# Initialise AWS clients outside the handler for connection reuse
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

# Read configuration from environment variables set by Terraform
TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "CloudTasks")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")


def calculate_word_count(text):
    """
    Calculate the word count of a given text string.

    Args:
        text (str): Input text to count words in.

    Returns:
        int: Number of words in the text.
    """
    if not text:
        return 0
    return len(text.split())


def estimate_complexity(title, description):
    """
    Estimate task complexity based on title and description length.
    Returns a complexity rating: low, medium, or high.

    Args:
        title (str): Task title.
        description (str): Task description.

    Returns:
        str: Complexity rating.
    """
    total_words = calculate_word_count(title) + calculate_word_count(description)
    if total_words < 10:
        return "low"
    elif total_words < 50:
        return "medium"
    else:
        return "high"


def lambda_handler(event, context):
    """
    Main Lambda handler function.
    Processes a newly created task by computing metadata and
    updating the task record in DynamoDB.

    Args:
        event (dict): Event data containing task_id, title, description, action.
        context: AWS Lambda context object.

    Returns:
        dict: Response with statusCode and processing results.
    """
    print(f"Received event: {json.dumps(event)}")

    task_id = event.get("task_id")
    title = event.get("title", "")
    description = event.get("description", "")
    action = event.get("action", "process_new_task")

    if not task_id:
        return {"statusCode": 400, "body": json.dumps({"error": "task_id is required"})}

    # Calculate task metadata
    word_count = calculate_word_count(description)
    complexity = estimate_complexity(title, description)
    processed_at = datetime.utcnow().isoformat()

    print(f"Processing task {task_id}: word_count={word_count}, complexity={complexity}")

    # Update the task record in DynamoDB with computed metadata
    try:
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET word_count = :wc, complexity = :cx, processed = :pr, processed_at = :pa",
            ExpressionAttributeValues={
                ":wc": word_count,
                ":cx": complexity,
                ":pr": True,
                ":pa": processed_at,
            },
        )
        print(f"Successfully updated task {task_id} in DynamoDB")
    except Exception as e:
        print(f"Error updating DynamoDB: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    # Send a processing completion notification via SNS
    if SNS_TOPIC_ARN:
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Task Processed: {title}",
                Message=(
                    f"Task '{title}' has been processed by Lambda.\n\n"
                    f"Task ID: {task_id}\n"
                    f"Word Count: {word_count}\n"
                    f"Complexity: {complexity}\n"
                    f"Processed At: {processed_at}"
                ),
            )
            print(f"SNS notification sent for task {task_id}")
        except Exception as e:
            # Log but do not fail on notification errors
            print(f"Warning: SNS notification failed: {str(e)}")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "task_id": task_id,
                "word_count": word_count,
                "complexity": complexity,
                "processed_at": processed_at,
                "message": "Task processed successfully",
            }
        ),
    }
