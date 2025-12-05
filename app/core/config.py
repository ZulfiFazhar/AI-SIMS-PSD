from pydantic_settings import BaseSettings
from typing import List
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

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL")
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"

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