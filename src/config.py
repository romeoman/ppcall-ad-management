"""
Configuration management for PPCall Ad Management system.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config(BaseSettings):
    """
    Application configuration with environment variable support.
    """
    
    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    projects_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "projects")
    
    # DataforSEO API
    dataforseo_login: Optional[str] = Field(default=None, env="DATAFORSEO_LOGIN")
    dataforseo_password: Optional[str] = Field(default=None, env="DATAFORSEO_PASSWORD")
    
    # Serper API
    serper_api_key: Optional[str] = Field(default=None, env="SERPER_API_KEY")
    
    # Firecrawl API
    firecrawl_api_key: Optional[str] = Field(default=None, env="FIRECRAWL_API_KEY")
    
    # API Configuration
    api_timeout: int = Field(default=30, description="API request timeout in seconds")
    api_retry_attempts: int = Field(default=3, description="Number of retry attempts for failed API calls")
    api_retry_delay: int = Field(default=1, description="Delay between retry attempts in seconds")
    
    # Data Processing
    batch_size: int = Field(default=100, description="Batch size for API requests")
    max_keywords_per_category: int = Field(default=500, description="Maximum keywords per category")
    min_search_volume: int = Field(default=10, description="Minimum search volume threshold")
    max_competition_score: float = Field(default=0.8, description="Maximum competition score (0-1)")
    
    # Output Configuration
    output_format: str = Field(default="csv", description="Default output format")
    include_headers: bool = Field(default=True, description="Include headers in output files")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    @validator("projects_dir", "project_root", pre=True)
    def ensure_path(cls, v):
        """Ensure paths are Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v
    
    @validator("dataforseo_login", "dataforseo_password")
    def validate_dataforseo_credentials(cls, v, values):
        """Validate DataforSEO credentials are provided together."""
        if "dataforseo_login" in values and values["dataforseo_login"] and not v:
            raise ValueError("DataforSEO password required when login is provided")
        if v and "dataforseo_login" in values and not values["dataforseo_login"]:
            raise ValueError("DataforSEO login required when password is provided")
        return v
    
    def has_dataforseo_credentials(self) -> bool:
        """Check if DataforSEO credentials are available."""
        return bool(self.dataforseo_login and self.dataforseo_password)
    
    def has_serper_credentials(self) -> bool:
        """Check if Serper API key is available."""
        return bool(self.serper_api_key)
    
    def has_firecrawl_credentials(self) -> bool:
        """Check if Firecrawl API key is available."""
        return bool(self.firecrawl_api_key)
    
    def get_api_headers(self, service: str) -> dict:
        """Get API headers for a specific service."""
        if service == "dataforseo":
            if not self.has_dataforseo_credentials():
                raise ValueError("DataforSEO credentials not configured")
            import base64
            auth = base64.b64encode(f"{self.dataforseo_login}:{self.dataforseo_password}".encode()).decode()
            return {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json"
            }
        elif service == "serper":
            if not self.has_serper_credentials():
                raise ValueError("Serper API key not configured")
            return {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
        elif service == "firecrawl":
            if not self.has_firecrawl_credentials():
                raise ValueError("Firecrawl API key not configured")
            return {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        (self.project_root / "logs").mkdir(exist_ok=True)
        (self.project_root / "examples").mkdir(exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create singleton instance
config = Config()

# Ensure directories exist
config.ensure_directories()