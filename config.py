"""
Configuration settings for Cyber AI Assistant
Render-optimized with environment variable handling
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent
    
    # App settings
    APP_NAME = os.getenv("APP_NAME", "Cyber AI Assistant")
    APP_VERSION = os.getenv("APP_VERSION", "3.0.0")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    API_KEYS = os.getenv("API_KEYS", "test-key,dev-key").split(",")
    
    # Render-specific settings
    IS_RENDER = os.getenv("RENDER", "False").lower() == "true"
    RENDER_PORT = int(os.getenv("PORT", "10000"))  # Render uses PORT env
    
    # Database (Render provides disk at /var/data)
    if IS_RENDER:
        DATA_DIR = Path("/var/data")
    else:
        DATA_DIR = BASE_DIR / "data"
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Database paths
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/cyberai.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Logging
    LOG_DIR = DATA_DIR / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "cyberai.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Cache
    CACHE_DIR = DATA_DIR / "cache"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
    
    # Scraper settings
    SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "10"))
    SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    SCRAPER_DELAY = float(os.getenv("SCRAPER_DELAY", "1.0"))
    
    # AI settings
    USE_ADVANCED_AI = os.getenv("USE_ADVANCED_AI", "True").lower() == "true"
    MAX_KEYWORDS = int(os.getenv("MAX_KEYWORDS", "5"))
    
    # Translation settings
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "bn")
    TRANSLATION_CACHE_SIZE = int(os.getenv("TRANSLATION_CACHE_SIZE", "1000"))
    
    # Image analysis
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/bmp"]
    
    # Chat history
    MAX_HISTORY_PER_SESSION = int(os.getenv("MAX_HISTORY_PER_SESSION", "50"))
    STORAGE_TYPE = os.getenv("STORAGE_TYPE", "sqlite")  # memory, sqlite, json
    
    @classmethod
    def get_port(cls) -> int:
        """Get the correct port for Render"""
        if cls.IS_RENDER:
            return cls.RENDER_PORT
        return cls.PORT
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development"""
        return cls.ENVIRONMENT == "development"

# Create config instance
config = Config()

# Log configuration on startup
logger.info(f"Environment: {config.ENVIRONMENT}")
logger.info(f"Data directory: {config.DATA_DIR}")
logger.info(f"Debug mode: {config.DEBUG}")
logger.info(f"Running on Render: {config.IS_RENDER}")
