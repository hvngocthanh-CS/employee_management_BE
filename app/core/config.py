"""
Application Configuration
==========================
Loads settings from environment variables (.env file)
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.
    Uses Pydantic for validation and type safety.
    """
    
    # === Application Settings ===
    PROJECT_NAME: str = "Employee Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # === Database Settings ===
    # Must be provided via environment variable (.env file)
    DATABASE_URL: str
    
    # === Security Settings ===
    # Must be provided via environment variable (.env file)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # === CORS Settings ===
    # Allowed origins for Cross-Origin Resource Sharing
    # Frontend (WPF) will use http://localhost:8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    class Config:
        # Read variables from .env file
        env_file = ".env"
        # Treat field names as case-sensitive
        case_sensitive = True


# Create a single instance to use throughout the app
settings = Settings()
