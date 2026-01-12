from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # Basic app settings
    app_name: str = os.getenv("APP_NAME")
    environment: str = os.getenv("ENVIRONMENT")
    debug: bool = os.getenv("DEBUG")
    version: str = os.getenv("VERSION")

    # Server settings
    host: str = os.getenv("HOST")
    port: int = os.getenv("PORT")

    # CORS settings
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS")

    # Security settings (production)
    allowed_hosts: str = os.getenv("ALLOWED_HOSTS")
    secret_key: str = os.getenv("SECRET_KEY")

    # ML settings
    ml_models_path: str = os.getenv("ML_MODELS_PATH")

    # Database settings
    database_url: str = os.getenv("DATABASE_URL")

    # Firebase settings
    firebase_credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH")
    firebase_project_id: str = os.getenv("FIREBASE_PROJECT_ID")

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL")
    log_format: str = "%(levelname)s - %(asctime)s - %(message)s"

    # Cloudflare R2 settings (S3 compatible storage)
    r2_account_id: str = os.getenv("R2_ACCOUNT_ID")
    r2_access_key_id: str = os.getenv("R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = os.getenv("R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str = os.getenv("R2_BUCKET_NAME")
    r2_public_url: str = os.getenv("R2_PUBLIC_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


settings = Settings()
