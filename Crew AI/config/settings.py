"""
Configuration settings for the Business Intelligence Platform
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-turbo-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///data/market_intelligence.db", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")
    
    # Crew AI Configuration
    crew_verbose: bool = Field(default=True, env="CREW_VERBOSE")
    crew_memory: bool = Field(default=True, env="CREW_MEMORY")
    crew_process: str = Field(default="sequential", env="CREW_PROCESS")
    
    # Data Collection Configuration
    data_collection_timeout: int = Field(default=30, env="DATA_COLLECTION_TIMEOUT")
    data_collection_retries: int = Field(default=3, env="DATA_COLLECTION_RETRIES")
    data_cache_ttl: int = Field(default=3600, env="DATA_CACHE_TTL")
    
    # Monitoring Configuration
    monitoring_interval: int = Field(default=3600, env="MONITORING_INTERVAL")
    monitoring_enabled: bool = Field(default=True, env="MONITORING_ENABLED")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")
    
    # Security Configuration
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # External API Keys (for production)
    yahoo_finance_api_key: Optional[str] = Field(default=None, env="YAHOO_FINANCE_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")
    twitter_api_key: Optional[str] = Field(default=None, env="TWITTER_API_KEY")
    
    # File Paths
    data_directory: str = Field(default="data", env="DATA_DIRECTORY")
    reports_directory: str = Field(default="reports", env="REPORTS_DIRECTORY")
    logs_directory: str = Field(default="logs", env="LOGS_DIRECTORY")
    
    # Performance Configuration
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=60, env="REQUEST_TIMEOUT")
    
    # Analysis Configuration
    analysis_confidence_threshold: float = Field(default=0.7, env="ANALYSIS_CONFIDENCE_THRESHOLD")
    trend_prediction_horizon: int = Field(default=24, env="TREND_PREDICTION_HORIZON")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.data_directory,
            self.reports_directory,
            self.logs_directory
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @property
    def database_config(self) -> dict:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "redis_url": self.redis_url,
            "data_directory": self.data_directory
        }
    
    @property
    def api_config(self) -> dict:
        """Get API configuration"""
        return {
            "host": self.api_host,
            "port": self.api_port,
            "debug": self.api_debug,
            "cors_origins": self.cors_origins
        }
    
    @property
    def crew_config(self) -> dict:
        """Get Crew AI configuration"""
        return {
            "verbose": self.crew_verbose,
            "memory": self.crew_memory,
            "process": self.crew_process,
            "model": self.openai_model,
            "temperature": self.openai_temperature
        }
    
    @property
    def data_collection_config(self) -> dict:
        """Get data collection configuration"""
        return {
            "timeout": self.data_collection_timeout,
            "retries": self.data_collection_retries,
            "cache_ttl": self.data_cache_ttl,
            "max_concurrent": self.max_concurrent_requests
        }
    
    @property
    def monitoring_config(self) -> dict:
        """Get monitoring configuration"""
        return {
            "enabled": self.monitoring_enabled,
            "interval": self.monitoring_interval,
            "confidence_threshold": self.analysis_confidence_threshold
        }
    
    @property
    def external_apis_config(self) -> dict:
        """Get external APIs configuration"""
        return {
            "yahoo_finance": self.yahoo_finance_api_key,
            "alpha_vantage": self.alpha_vantage_api_key,
            "news_api": self.news_api_key,
            "twitter": self.twitter_api_key
        } 