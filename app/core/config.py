"""
Configuration management for Bookology Backend.

This module centralizes all configuration settings and environment variables
for the Bookology application, following the 12-factor app methodology.
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Application settings configuration.
    
    This class handles all environment variables and configuration settings
    for the Bookology backend application. It uses environment variables
    with sensible defaults where appropriate.
    """
    
    # API Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # OpenAI DALL-E 3 API Configuration (uses existing OPENAI_API_KEY)
    # LEONARDO_API_KEY removed - now using OPENAI_API_KEY for both text and image generation
    
    # Database Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    SUPABASE_CONNECTION_STRING: str = os.getenv("SUPABASE_CONNECTION_STRING", "")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    RELOAD: bool = os.getenv("RELOAD", "False").lower() in ("true", "1", "yes")
    
    # Vector Store Configuration
    VECTOR_COLLECTION_NAME: str = os.getenv("VECTOR_COLLECTION_NAME", "chapter_chunks")
    VECTOR_SEARCH_K: int = int(os.getenv("VECTOR_SEARCH_K", "5"))
    
    # Optional local vector search (disabled by default to avoid heavy deps at runtime)
    ENABLE_LOCAL_VECTOR_SEARCH: bool = os.getenv("ENABLE_LOCAL_VECTOR_SEARCH", "False").lower() in ("true", "1", "yes")
    
    # Database URL compatibility (for components expecting DATABASE_URL)
    # Falls back to Supabase connection string if DATABASE_URL is not explicitly set
    DATABASE_URL: str = os.getenv("DATABASE_URL", os.getenv("SUPABASE_CONNECTION_STRING", ""))
    
    # Concurrency Configuration
    MAX_CONCURRENT_LLM_CALLS: int = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "5"))
    MAX_CONCURRENT_DB_CONNECTIONS: int = int(os.getenv("MAX_CONCURRENT_DB_CONNECTIONS", "20"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # CORS Configuration
    # Default to empty list in production to enforce least-privilege unless explicitly set
    ALLOWED_ORIGINS: list[str] = [o for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o]
    @property
    def cors_allow_all(self) -> bool:
        return len(self.ALLOWED_ORIGINS) == 0
    
    # Template Configuration
    TEMPLATES_DIR: str = os.getenv("TEMPLATES_DIR", "templates")
    
    def validate_required_settings(self) -> None:
        """
        Validate that all required environment variables are set.
        
        Raises:
            ValueError: If any required environment variable is missing.
        """
        required_settings = [
            ("OPENAI_API_KEY", self.OPENAI_API_KEY),
            ("SUPABASE_URL", self.SUPABASE_URL),
            ("SUPABASE_SERVICE_KEY", self.SUPABASE_SERVICE_KEY),
            ("SUPABASE_CONNECTION_STRING", self.SUPABASE_CONNECTION_STRING),
        ]
        
        missing_settings = [
            name for name, value in required_settings if not value
        ]
        
        if missing_settings:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_settings)}"
            )
    
    def get_postgres_connection_string(self) -> str:
        """
        Get the PostgreSQL connection string formatted for psycopg3.
        
        Returns:
            str: Properly formatted connection string for psycopg3.
        """
        connection_string = self.SUPABASE_CONNECTION_STRING
        
        # Convert standard PostgreSQL URL to psycopg3 format
        if connection_string and connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace(
                "postgresql://", "postgresql+psycopg://"
            )
        
        return connection_string


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings instance (cached).
    
    This function returns a cached instance of the Settings class,
    ensuring that environment variables are only read once during
    the application lifecycle.
    
    Returns:
        Settings: The application settings instance.
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()