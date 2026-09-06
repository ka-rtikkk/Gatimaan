"""
Gatimaan Backend Configuration
Loads settings from environment variables / .env file
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # App
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # CORS
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "gatimaan-prototype-secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # Prototype
    PROTOTYPE_MODE: bool = os.getenv("PROTOTYPE_MODE", "true").lower() == "true"
    DATA_LABEL: str = os.getenv("DATA_LABEL", "SIMULATED_PROTOTYPE_DATA")


settings = Settings()
