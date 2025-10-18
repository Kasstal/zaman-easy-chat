from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    OPENAI_API_KEY: Optional[str] = None
    DATABASE_URL: str = "sqlite+aiosqlite:///./zaman.db"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
