import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./land_records.db"
    SECRET_KEY: str = "sih_super_secret_jwt_key_2026_land_digitization"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Upload and Preprocessed Directories
    UPLOAD_DIR: str = "uploads"
    PREPROCESSED_DIR: str = "preprocessed"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.PREPROCESSED_DIR).mkdir(parents=True, exist_ok=True)
