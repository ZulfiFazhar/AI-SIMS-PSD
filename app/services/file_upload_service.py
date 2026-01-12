import os
import logging
from typing import List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid

from app.core.object_storage import r2_client

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads to Cloudflare R2"""

    def __init__(self):
        """Initialize file upload service with R2 client"""
        if not r2_client.is_configured:
            logger.warning("R2 client is not configured. File uploads will fail.")

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "tenants",
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: int = 10,
    ) -> str:
        """
        Upload single file to R2.

        Args:
            file: FastAPI UploadFile object
            folder: Folder path in bucket (e.g., 'tenants', 'tenants/logos')
            allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.jpg'])
            max_size_mb: Maximum file size in MB

        Returns:
            Public URL of uploaded file

        Raises:
            ValueError: If file validation fails
            Exception: If upload fails
        """
        try:
            # Check if R2 client is configured
            if not r2_client.is_configured:
                raise Exception(
                    "R2 client not configured. Check R2 environment variables."
                )

            # Validate filename exists
            if not file.filename:
                raise ValueError("File name is required")

            logger.info(f"Starting upload for file: {file.filename}")

            # Validate file extension
            if allowed_extensions:
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in allowed_extensions:
                    raise ValueError(
                        f"File extension {file_ext} tidak diizinkan. "
                        f"Hanya {', '.join(allowed_extensions)} yang diperbolehkan."
                    )

            # Read file content
            content = await file.read()
            size_mb = len(content) / (1024 * 1024)

            logger.info(f"File size: {size_mb:.2f}MB")

            # Check file size
            if size_mb > max_size_mb:
                raise ValueError(
                    f"Ukuran file {size_mb:.2f}MB melebihi batas maksimal {max_size_mb}MB"
                )

            # Validate content is not empty
            if len(content) == 0:
                raise ValueError("File is empty")

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_ext = os.path.splitext(file.filename)[1]
            safe_filename = f"{timestamp}_{unique_id}{file_ext}"

            object_key = f"{folder}/{safe_filename}"

            logger.info(
                f"Uploading to R2: {object_key} (Bucket: {r2_client.bucket_name})"
            )

            response = r2_client.client.put_object(
                Bucket=r2_client.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=file.content_type or "application/octet-stream",
            )

            logger.info(
                f"R2 response: {response.get('ResponseMetadata', {}).get('HTTPStatusCode')}"
            )

            public_url = f"{r2_client.public_url}/{object_key}"
            logger.info(f"File uploaded successfully: {public_url}")

            return public_url

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            logger.error(f"R2 ClientError [{error_code}]: {error_message}")
            raise Exception(f"Gagal mengupload file ke R2: {error_message}")
        except Exception as e:
            logger.error(f"Upload error: {type(e).__name__} - {str(e)}", exc_info=True)
            raise Exception(f"Gagal mengupload file: {str(e)}")

    async def upload_multiple_files(
        self,
        files: List[UploadFile],
        folder: str = "tenants",
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: int = 10,
    ) -> List[str]:
        """
        Upload multiple files to R2.

        Args:
            files: List of FastAPI UploadFile objects
            folder: Folder path in bucket
            allowed_extensions: List of allowed extensions
            max_size_mb: Maximum file size per file in MB

        Returns:
            List of public URLs of uploaded files
        """
        uploaded_urls = []

        for file in files:
            try:
                url = await self.upload_file(
                    file, folder, allowed_extensions, max_size_mb
                )
                uploaded_urls.append(url)
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                # Continue uploading other files
                continue

        return uploaded_urls

    def delete_file(self, file_url: str) -> bool:
        """
        Delete file from R2.

        Args:
            file_url: Public URL of the file

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            object_key = file_url.replace(f"{r2_client.public_url}/", "")

            r2_client.client.delete_object(Bucket=r2_client.bucket_name, Key=object_key)
            logger.info(f"File deleted successfully: {object_key}")
            return True

        except ClientError as e:
            logger.error(f"R2 delete error: {e}")
            return False
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def generate_presigned_url(
        self, file_url: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for private file access.

        Args:
            file_url: Public URL of the file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if failed
        """
        try:
            object_key = file_url.replace(f"{r2_client.public_url}/", "")

            url = r2_client.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": r2_client.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None


# Singleton instance
file_upload_service = FileUploadService()
