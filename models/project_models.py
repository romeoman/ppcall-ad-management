"""Project configuration and management models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path
from enum import Enum


class ProjectStatus(str, Enum):
    """Project status options."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    """Types of projects supported."""
    SINGLE_CAMPAIGN = "single_campaign"
    MULTI_CAMPAIGN = "multi_campaign"
    TEMPLATE = "template"
    CLONE = "clone"


class LocationType(str, Enum):
    """Location targeting types."""
    CITY = "city"
    STATE = "state"
    COUNTRY = "country"
    ZIP_CODE = "zip_code"
    RADIUS = "radius"
    CUSTOM = "custom"


class ProjectInputs(BaseModel):
    """Input files and data for a project."""
    seed_keywords_file: Optional[Path] = None
    negative_keywords_file: Optional[Path] = None
    locations_file: Optional[Path] = None
    categories_file: Optional[Path] = None
    competitor_urls_file: Optional[Path] = None
    spyfu_csv_file: Optional[Path] = None
    
    # Direct input data (alternative to files)
    seed_keywords: List[str] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    competitor_urls: List[str] = Field(default_factory=list)
    
    @field_validator('seed_keywords_file', 'negative_keywords_file', 'locations_file', 
                   'categories_file', 'competitor_urls_file', 'spyfu_csv_file')
    def validate_file_exists(cls, v):
        """Check if input file exists."""
        if v and not v.exists():
            raise ValueError(f"Input file does not exist: {v}")
        return v
    
    def has_seed_keywords(self) -> bool:
        """Check if project has seed keywords."""
        return bool(self.seed_keywords or self.seed_keywords_file)
    
    def has_locations(self) -> bool:
        """Check if project has location data."""
        return bool(self.locations or self.locations_file)
    
    def get_all_input_files(self) -> List[Path]:
        """Get list of all input files."""
        files = []
        for field in ['seed_keywords_file', 'negative_keywords_file', 'locations_file',
                     'categories_file', 'competitor_urls_file', 'spyfu_csv_file']:
            file_path = getattr(self, field)
            if file_path:
                files.append(file_path)
        return files


class ProjectOutputs(BaseModel):
    """Output configuration for a project."""
    output_directory: Path
    keywords_csv: Optional[str] = Field(default="keywords.csv")
    negative_keywords_csv: Optional[str] = Field(default="negative_keywords.csv")
    ad_groups_csv: Optional[str] = Field(default="ad_groups.csv")
    competitor_analysis_csv: Optional[str] = Field(default="competitor_analysis.csv")
    landing_pages_csv: Optional[str] = Field(default="landing_pages.csv")
    consolidated_csv: Optional[str] = Field(default="consolidated_output.csv")
    
    # Google Ads specific outputs
    google_ads_directory: Optional[Path] = None
    create_editor_files: bool = Field(default=True)
    create_import_files: bool = Field(default=True)
    
    @field_validator('output_directory', 'google_ads_directory')
    def create_directory(cls, v):
        """Ensure output directory exists."""
        if v:
            v = Path(v)
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_output_path(self, filename: str) -> Path:
        """Get full path for an output file."""
        return self.output_directory / filename


class APIConfig(BaseModel):
    """API configuration for external services."""
    data4seo_login: Optional[str] = Field(None, description="Data4SEO API login")
    data4seo_password: Optional[str] = Field(None, description="Data4SEO API password")
    serp_api_key: Optional[str] = Field(None, description="SERP API key")
    firecrawl_api_key: Optional[str] = Field(None, description="FireCrawl API key")
    
    # API limits and settings
    max_concurrent_requests: int = Field(default=5, ge=1, le=20)
    request_timeout: int = Field(default=30, ge=10, le=120)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    rate_limit_delay: float = Field(default=1.0, ge=0, le=10)
    
    def has_data4seo_credentials(self) -> bool:
        """Check if Data4SEO credentials are configured."""
        return bool(self.data4seo_login and self.data4seo_password)
    
    def has_serp_credentials(self) -> bool:
        """Check if SERP API credentials are configured."""
        return bool(self.serp_api_key)
    
    def has_firecrawl_credentials(self) -> bool:
        """Check if FireCrawl credentials are configured."""
        return bool(self.firecrawl_api_key)


class ProcessingConfig(BaseModel):
    """Configuration for data processing."""
    min_search_volume: int = Field(default=10, ge=0)
    max_search_volume: Optional[int] = Field(None, ge=1)
    min_cpc: float = Field(default=0.0, ge=0)
    max_cpc: Optional[float] = Field(None, ge=0)
    max_competition: float = Field(default=1.0, ge=0, le=1)
    
    # Keyword expansion settings
    expand_seed_keywords: bool = Field(default=True)
    max_expansions_per_seed: int = Field(default=50, ge=1, le=500)
    include_questions: bool = Field(default=True)
    include_long_tail: bool = Field(default=True)
    
    # Ad group settings
    max_keywords_per_ad_group: int = Field(default=20, ge=1, le=100)
    group_by_category: bool = Field(default=True)
    group_by_location: bool = Field(default=True)
    
    # Negative keywords settings
    auto_generate_negatives: bool = Field(default=True)
    negative_keyword_sources: List[str] = Field(
        default_factory=lambda: ["competitor_brand", "irrelevant", "low_intent"]
    )
    
    @field_validator('max_cpc')
    def validate_max_cpc(cls, v, values):
        """Ensure max_cpc is greater than min_cpc."""
        if v is not None and 'min_cpc' in values and v < values['min_cpc']:
            raise ValueError("max_cpc must be greater than min_cpc")
        return v


class ProjectMetadata(BaseModel):
    """Metadata for project tracking."""
    project_id: str = Field(..., pattern="^[a-zA-Z0-9_-]+$")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="system")
    version: str = Field(default="1.0.0")
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # Statistics
    total_keywords_processed: int = Field(default=0, ge=0)
    total_api_calls: int = Field(default=0, ge=0)
    processing_time_seconds: float = Field(default=0.0, ge=0)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to the project."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.update_timestamp()


class ProjectConfig(BaseModel):
    """Complete project configuration."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    type: ProjectType = Field(default=ProjectType.SINGLE_CAMPAIGN)
    status: ProjectStatus = Field(default=ProjectStatus.DRAFT)
    
    # Configuration components
    inputs: ProjectInputs
    outputs: ProjectOutputs
    api_config: APIConfig
    processing_config: ProcessingConfig
    metadata: ProjectMetadata
    
    # Campaign settings
    campaign_name: str = Field(..., min_length=1, max_length=255)
    target_locations: List[str] = Field(default_factory=list)
    location_type: LocationType = Field(default=LocationType.CITY)
    language: str = Field(default="en")
    currency: str = Field(default="USD")
    
    # Clone/template settings
    parent_project_id: Optional[str] = None
    is_template: bool = Field(default=False)
    
    @field_validator('name', 'campaign_name')
    def clean_names(cls, v):
        """Clean and validate names."""
        # Remove characters that might cause issues
        invalid_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            v = v.replace(char, '')
        return v.strip()
    
    def validate_ready_for_processing(self) -> List[str]:
        """Check if project is ready for processing."""
        errors = []
        
        if not self.inputs.has_seed_keywords():
            errors.append("No seed keywords provided")
        
        if not self.api_config.has_data4seo_credentials() and not self.api_config.has_serp_credentials():
            errors.append("No API credentials configured")
        
        if self.processing_config.max_search_volume and \
           self.processing_config.max_search_volume < self.processing_config.min_search_volume:
            errors.append("max_search_volume must be greater than min_search_volume")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for saving."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create from dictionary."""
        # Convert string paths back to Path objects
        if 'inputs' in data:
            for field in ['seed_keywords_file', 'negative_keywords_file', 'locations_file',
                         'categories_file', 'competitor_urls_file', 'spyfu_csv_file']:
                if field in data['inputs'] and data['inputs'][field]:
                    data['inputs'][field] = Path(data['inputs'][field])
        
        if 'outputs' in data:
            if 'output_directory' in data['outputs']:
                data['outputs']['output_directory'] = Path(data['outputs']['output_directory'])
            if 'google_ads_directory' in data['outputs'] and data['outputs']['google_ads_directory']:
                data['outputs']['google_ads_directory'] = Path(data['outputs']['google_ads_directory'])
        
        return cls(**data)
    
