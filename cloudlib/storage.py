"""
CloudStorageManager - Manages AWS S3 storage operations.

Provides methods for uploading, downloading, deleting, and listing
objects in S3 buckets with automatic key generation and error handling.
"""
import os
import uuid
from datetime import datetime
from botocore.exceptions import ClientError


class CloudStorageManager:
    """
    Object-oriented interface for AWS S3 storage operations.
    Handles file uploads, downloads, deletions, listing, and
    presigned URL generation for secure temporary access.

    Attributes:
        s3_client: boto3 S3 client instance.
        region (str): AWS region name.
    """

    def __init__(self, session, region):
        """
        Initialize CloudStorageManager with an AWS session.

        Args:
            session (boto3.Session): Active boto3 session.
            region (str): AWS region name.
        """
        self.s3_client = session.client("s3", region_name=region)
        self.region = region

    def upload_file(self, bucket_name, file_obj, original_filename, folder="attachments"):
        """
        Upload a file object to an S3 bucket with a unique generated key.

        Args:
            bucket_name (str): Target S3 bucket name.
            file_obj: File-like object to upload (e.g., from Flask request.files).
            original_filename (str): Original name of the file for extension extraction.
            folder (str): S3 key prefix/folder. Defaults to 'attachments'.

        Returns:
            dict: Result containing 'success' boolean, 'key' (S3 object key),
                  'bucket', 'original_filename', and 'uploaded_at' on success.
                  Contains 'error' message string on failure.
        """
        # Generate a unique key to prevent filename collisions
        file_ext = os.path.splitext(original_filename)[1]
        unique_key = f"{folder}/{uuid.uuid4().hex}{file_ext}"

        try:
            # Determine content type from file object if available
            content_type = (
                file_obj.content_type
                if hasattr(file_obj, "content_type")
                else "application/octet-stream"
            )
            self.s3_client.upload_fileobj(
                file_obj,
                bucket_name,
                unique_key,
                ExtraArgs={"ContentType": content_type},
            )
            return {
                "success": True,
                "key": unique_key,
                "bucket": bucket_name,
                "original_filename": original_filename,
                "uploaded_at": datetime.utcnow().isoformat(),
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def download_file(self, bucket_name, key):
        """
        Download a file from an S3 bucket.

        Args:
            bucket_name (str): Source S3 bucket name.
            key (str): S3 object key to download.

        Returns:
            dict: Result with 'success', 'body' (StreamingBody),
                  'content_type', and 'content_length' on success.
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key)
            return {
                "success": True,
                "body": response["Body"],
                "content_type": response.get("ContentType", "application/octet-stream"),
                "content_length": response.get("ContentLength", 0),
            }
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def delete_file(self, bucket_name, key):
        """
        Delete a file from an S3 bucket.

        Args:
            bucket_name (str): S3 bucket name.
            key (str): S3 object key to delete.

        Returns:
            dict: Result with 'success' and 'deleted_key'.
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=key)
            return {"success": True, "deleted_key": key}
        except ClientError as e:
            return {"success": False, "error": str(e)}

    def generate_presigned_url(self, bucket_name, key, expiration=3600):
        """
        Generate a presigned URL for temporary access to an S3 object.

        Args:
            bucket_name (str): S3 bucket name.
            key (str): S3 object key.
            expiration (int): URL expiration time in seconds. Default 3600 (1 hour).

        Returns:
            str: Presigned URL string, or None on error.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError:
            return None

    def list_files(self, bucket_name, prefix=""):
        """
        List all files in an S3 bucket matching an optional prefix.

        Args:
            bucket_name (str): S3 bucket name.
            prefix (str): Key prefix filter. Default empty (all files).

        Returns:
            list: List of S3 object metadata dictionaries.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return response.get("Contents", [])
        except ClientError:
            return []

    def health_check(self):
        """
        Verify S3 service connectivity.

        Returns:
            bool: True if S3 is accessible, False otherwise.
        """
        try:
            self.s3_client.list_buckets()
            return True
        except ClientError:
            return False
