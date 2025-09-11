"""Configuration management for the Daily API Pipeline"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Swiss Ephemeris API
    swiss_api_base_url: str = Field(
        default="https://api.swissephemeris.com/v1",
        description="Swiss Ephemeris API base URL"
    )
    swiss_api_key: str = Field(
        ...,
        description="Swiss Ephemeris API key"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key"
    )
    openai_org_id: Optional[str] = Field(
        default=None,
        description="OpenAI Organization ID"
    )
    
    # OpenAI Assistant IDs
    astro_interpreter_assistant_id: str = Field(
        ...,
        description="Assistant ID for astrological interpretation"
    )
    email_formatter_assistant_id: str = Field(
        ...,
        description="Assistant ID for email formatting"
    )
    cypher_generator_assistant_id: str = Field(
        ...,
        description="Assistant ID for Cypher query generation"
    )
    
    # Neo4j Configuration
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j database URI"
    )
    neo4j_username: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        ...,
        description="Neo4j password"
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )
    
    # Email Configuration
    smtp_host: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host"
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port"
    )
    smtp_username: str = Field(
        ...,
        description="SMTP username"
    )
    smtp_password: str = Field(
        ...,
        description="SMTP password"
    )
    email_from: str = Field(
        ...,
        description="Sender email address"
    )
    email_to: str = Field(
        ...,
        description="Recipient email address"
    )
    
    # Location Configuration
    latitude: float = Field(
        default=40.7128,
        description="Latitude for astronomical calculations"
    )
    longitude: float = Field(
        default=-74.0060,
        description="Longitude for astronomical calculations"
    )
    timezone: str = Field(
        default="America/New_York",
        description="Timezone for calculations"
    )
    
    # Scheduling Configuration
    schedule_hour: int = Field(
        default=6,
        ge=0,
        le=23,
        description="Hour to run daily job (0-23)"
    )
    schedule_minute: int = Field(
        default=0,
        ge=0,
        le=59,
        description="Minute to run daily job (0-59)"
    )
    planetary_hour_scheduling: bool = Field(
        default=False,
        description="Use planetary hour calculations for scheduling"
    )
    
    # Application Configuration
    app_env: str = Field(
        default="development",
        description="Application environment"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retries for failed operations"
    )
    retry_delay: int = Field(
        default=5,
        ge=0,
        description="Initial retry delay in seconds"
    )
    exponential_backoff: bool = Field(
        default=True,
        description="Use exponential backoff for retries"
    )
    
    @validator("schedule_hour")
    def validate_hour(cls, v):
        if not 0 <= v <= 23:
            raise ValueError("Schedule hour must be between 0 and 23")
        return v
    
    @validator("schedule_minute")
    def validate_minute(cls, v):
        if not 0 <= v <= 59:
            raise ValueError("Schedule minute must be between 0 and 59")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.app_env.lower() == "development"


# Create global settings instance
settings = Settings()


# Utility function to get project root
def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent
