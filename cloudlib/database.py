"""
CloudDatabaseManager - Manages AWS DynamoDB operations.

Provides methods for CRUD operations on DynamoDB tables with
automatic type handling and error management.
"""
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr


class CloudDatabaseManager:
    """
    Object-oriented interface for AWS DynamoDB operations.
    Supports creating tables, and performing CRUD operations
    (put, get, update, delete, scan, query) on DynamoDB items.

    Attributes:
        dynamodb_client: boto3 DynamoDB client.
        dynamodb_resource: boto3 DynamoDB resource for higher-level access.
        region (str): AWS region name.
    """

    def __init__(self, session, region):
        """
        Initialize CloudDatabaseManager with an AWS session.

        Args:
            session (boto3.Session): Active boto3 session.
            region (str): AWS region name.
        """
        self.dynamodb_client = session.client("dynamodb", region_name=region)
        self.dynamodb_resource = session.resource("dynamodb", region_name=region)
        self.region = region

    def create_table(self, table_name, partition_key, partition_key_type="S"):
        """
        Create a new DynamoDB table with on-demand billing.

        Args:
            table_name (str): Name of the table to create.
            partition_key (str): Name of the partition (hash) key attribute.
            partition_key_type (str): Key type - 'S' (String), 'N' (Number). Default 'S'.

        Returns:
            dict: Result with 'success' and 'table_name' or 'error'.
        """
        try:
            self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": partition_key, "AttributeType": partition_key_type}
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            # Wait for the table to become active
            waiter = self.dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=table_name)
            return {"success": True, "table_name": table_name}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def put_item(self, table_name, item):
        """
        Insert or replace an item in a DynamoDB table.

        Args:
            table_name (str): Target table name.
            item (dict): Item data as key-value pairs.

        Returns:
            dict: Result with 'success' boolean.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)
            table.put_item(Item=item)
            return {"success": True, "item": item}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def get_item(self, table_name, key):
        """
        Retrieve a single item from a DynamoDB table by its primary key.

        Args:
            table_name (str): Table name.
            key (dict): Primary key, e.g., {'task_id': '123'}.

        Returns:
            dict: The item if found, or None.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)
            response = table.get_item(Key=key)
            return response.get("Item")
        except ClientError:
            return None

    def update_item(self, table_name, key, update_data):
        """
        Update specific attributes of an existing item in DynamoDB.

        Dynamically builds the UpdateExpression from the provided update_data
        dictionary, supporting any number of attribute updates in one call.

        Args:
            table_name (str): Table name.
            key (dict): Primary key of the item to update.
            update_data (dict): Attributes to update as key-value pairs.

        Returns:
            dict: Result with 'success' and updated 'attributes', or 'error'.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)

            # Dynamically build the update expression from provided data
            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}

            for idx, (attr_key, attr_value) in enumerate(update_data.items()):
                placeholder = f":val{idx}"
                name_placeholder = f"#attr{idx}"
                update_expr_parts.append(f"{name_placeholder} = {placeholder}")
                expr_attr_values[placeholder] = attr_value
                expr_attr_names[name_placeholder] = attr_key

            update_expression = "SET " + ", ".join(update_expr_parts)

            response = table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expr_attr_values,
                ExpressionAttributeNames=expr_attr_names,
                ReturnValues="ALL_NEW",
            )
            return {"success": True, "attributes": response.get("Attributes")}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def delete_item(self, table_name, key):
        """
        Delete an item from a DynamoDB table.

        Args:
            table_name (str): Table name.
            key (dict): Primary key of the item to delete.

        Returns:
            dict: Result with 'success' boolean.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)
            table.delete_item(Key=key)
            return {"success": True}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def scan_table(self, table_name, filter_expression=None):
        """
        Scan an entire DynamoDB table, optionally filtering results.

        Args:
            table_name (str): Table name to scan.
            filter_expression: Optional boto3 filter expression (e.g., Attr('status').eq('pending')).

        Returns:
            list: List of matching item dictionaries.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)
            scan_kwargs = {}
            if filter_expression is not None:
                scan_kwargs["FilterExpression"] = filter_expression

            items = []
            # Handle pagination for large tables
            while True:
                response = table.scan(**scan_kwargs)
                items.extend(response.get("Items", []))
                if "LastEvaluatedKey" not in response:
                    break
                scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

            return items
        except ClientError:
            return []

    def query_table(self, table_name, key_condition):
        """
        Query a DynamoDB table using a key condition expression.

        Args:
            table_name (str): Table name.
            key_condition: boto3 key condition expression.

        Returns:
            list: List of matching items.
        """
        try:
            table = self.dynamodb_resource.Table(table_name)
            response = table.query(KeyConditionExpression=key_condition)
            return response.get("Items", [])
        except ClientError:
            return []

    def health_check(self):
        """
        Verify DynamoDB service connectivity.

        Returns:
            bool: True if DynamoDB is accessible, False otherwise.
        """
        try:
            self.dynamodb_client.list_tables(Limit=1)
            return True
        except ClientError:
            return False
