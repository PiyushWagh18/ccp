"""
S3 service for CloudTask Manager.
Wraps cloudlib.CloudStorageManager with application-specific attachment operations.
"""
import os
from app.services import get_cloud_manager


class TaskStorageService:
    """
    Application service layer for S3 file attachment operations.
    Uses the cloudlib CloudStorageManager to upload, download,
    and delete task file attachments in the designated S3 bucket.
    """

    def __init__(self):
        """Initialise with shared CloudManager and bucket name from config."""
        cloud = get_cloud_manager()
        self.storage = cloud.storage
        self.bucket_name = os.environ.get("S3_BUCKET", "cloudtask-attachments-614939596951")

    def upload_attachment(self, file_obj, filename):
        """
        Upload a file attachment for a task to S3.

        Args:
            file_obj: File-like object from Flask request.files.
            filename (str): Original filename.

        Returns:
            dict: Upload result with 'success', 'key', and metadata.
        """
        return self.storage.upload_file(
            self.bucket_name, file_obj, filename, folder="task-attachments"
        )

    def download_attachment(self, key):
        """
        Download a file attachment from S3.

        Args:
            key (str): S3 object key of the attachment.

        Returns:
            dict: Result with 'success' and file 'body' stream.
        """
        return self.storage.download_file(self.bucket_name, key)

    def delete_attachment(self, key):
        """
        Delete a file attachment from S3.

        Args:
            key (str): S3 object key to delete.

        Returns:
            dict: Result with 'success' boolean.
        """
        return self.storage.delete_file(self.bucket_name, key)

    def get_attachment_url(self, key, expiration=3600):
        """
        Generate a presigned URL for temporary attachment access.

        Args:
            key (str): S3 object key.
            expiration (int): URL validity in seconds. Default 3600.

        Returns:
            str: Presigned URL or None on failure.
        """
        return self.storage.generate_presigned_url(
            self.bucket_name, key, expiration
        )
