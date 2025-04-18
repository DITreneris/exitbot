"""
Configuration settings for the ExitBot application
"""
import os
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "ExitBot"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "testsecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///./exitbot.db"
    )
    
    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
    
    # Groq (New)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    # LLM Provider: 'ollama' or 'groq'
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1024")) # Max tokens for LLM response
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # This allows extra fields in the environment
    }

settings = Settings() 