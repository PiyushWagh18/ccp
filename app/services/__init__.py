"""
Service layer initialisation for CloudTask Manager.
Provides a shared CloudManager singleton used by all service modules.
"""
import os
from cloudlib import CloudManager

# Module-level singleton CloudManager instance (lazy-initialised)
_cloud_manager = None


def get_cloud_manager():
    """
    Return a shared CloudManager instance, creating it on first call.
    Uses AWS credentials from environment variables when available;
    falls back to IAM instance profile when running on EC2.

    Returns:
        CloudManager: Configured cloud manager instance.
    """
    global _cloud_manager
    if _cloud_manager is None:
        _cloud_manager = CloudManager(
            region=os.environ.get("AWS_REGION", "eu-north-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
    return _cloud_manager
