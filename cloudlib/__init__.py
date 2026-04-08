"""
CloudLib - A Python library for AWS cloud service management.

Provides object-oriented abstractions over AWS services including
S3, DynamoDB, SNS, Lambda, and CloudWatch. Designed for building
cloud-native Python applications with clean, reusable interfaces.

Usage:
    from cloudlib import CloudManager

    cloud = CloudManager(region="eu-north-1")
    cloud.storage.upload_file("my-bucket", file_obj, "file.txt")
    cloud.database.put_item("MyTable", {"id": "1", "name": "Test"})
"""
from cloudlib.cloud_manager import CloudManager
from cloudlib.storage import CloudStorageManager
from cloudlib.database import CloudDatabaseManager
from cloudlib.notifications import CloudNotificationManager
from cloudlib.logger import CloudLogger
from cloudlib.compute import CloudComputeManager

__version__ = "1.0.0"
__all__ = [
    "CloudManager",
    "CloudStorageManager",
    "CloudDatabaseManager",
    "CloudNotificationManager",
    "CloudLogger",
    "CloudComputeManager",
]
