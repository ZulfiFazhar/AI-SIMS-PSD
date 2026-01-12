import boto3
import logging
from typing import Optional
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class R2Client:
    """Singleton class for Cloudflare R2 (S3-compatible) client"""

    _instance: Optional["R2Client"] = None
    _client: Optional[BaseClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(R2Client, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance

    def _initialize_client(self):
        """Initialize R2 client with configuration validation"""
        try:
            required_configs = {
                "R2_ACCOUNT_ID": settings.r2_account_id,
                "R2_ACCESS_KEY_ID": settings.r2_access_key_id,
                "R2_SECRET_ACCESS_KEY": settings.r2_secret_access_key,
                "R2_BUCKET_NAME": settings.r2_bucket_name,
                "R2_PUBLIC_URL": settings.r2_public_url,
            }

            missing_configs = [
                key for key, value in required_configs.items() if not value
            ]

            if missing_configs:
                logger.warning(
                    f"R2 configuration incomplete. Missing: {', '.join(missing_configs)}"
                )
                self._client = None
                return

            # Build endpoint URL
            endpoint_url = f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"

            # Initialize boto3 S3 client for R2
            self._client = boto3.client(
                service_name="s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=settings.r2_access_key_id,
                aws_secret_access_key=settings.r2_secret_access_key,
                region_name="auto",
            )

            # Test connection
            try:
                self._client.head_bucket(Bucket=settings.r2_bucket_name)
                logger.info(
                    f"R2 client initialized successfully. Bucket: {settings.r2_bucket_name}"
                )
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                if error_code == "404":
                    logger.error(f"R2 bucket '{settings.r2_bucket_name}' not found")
                elif error_code == "403":
                    logger.error(
                        f"Access denied to R2 bucket '{settings.r2_bucket_name}'"
                    )
                else:
                    logger.error(f"R2 connection test failed: {e}")
                self._client = None

        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}", exc_info=True)
            self._client = None

    @property
    def client(self) -> Optional[BaseClient]:
        """Get R2 client instance"""
        return self._client

    @property
    def is_configured(self) -> bool:
        """Check if R2 is properly configured and connected"""
        return self._client is not None

    @property
    def bucket_name(self) -> str:
        """Get configured bucket name"""
        return settings.r2_bucket_name

    @property
    def public_url(self) -> str:
        """Get public URL for R2 bucket"""
        return settings.r2_public_url

    def reconnect(self):
        """Reconnect to R2 (useful for error recovery)"""
        logger.info("Reconnecting to R2...")
        self._initialize_client()


# Singleton instance
r2_client = R2Client()
