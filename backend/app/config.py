"""
Application configuration settings
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DB_PATH: Path = BASE_DIR / "data" / "courses.db"
    MODELS_DIR: Path = BASE_DIR / "models"
    PLOTS_DIR: Path = BASE_DIR / "plots"
    FRONTEND_BUILD_DIR: Path = BASE_DIR / "frontend" / "dist"

    # Environment
    ENVIRONMENT: str = "development"

    # CORS - Allow local development and production domains
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "UC Berkeley Course Difficulty Prediction API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Predict course GPA based on grade distributions and grading structure"

    # Groq API for LLM analysis (optional)
    GROQ_API_KEY: str = ""  # Set via environment variable

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
