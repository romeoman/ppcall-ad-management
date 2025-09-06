"""
Project Configuration Management

Handles loading, saving, and validation of project configurations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
import hashlib


@dataclass
class LocationSettings:
    """Location targeting settings."""
    type: str = "cities"  # cities, zipcodes, or both
    include_surrounding: bool = True
    radius_miles: int = 25
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationSettings':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class KeywordSettings:
    """Keyword generation settings."""
    match_types: List[str] = field(default_factory=lambda: ["exact", "phrase", "broad"])
    include_variations: bool = True
    min_search_volume: int = 10
    max_cpc: float = 50.00
    max_competition: float = 1.0
    include_questions: bool = True
    include_long_tail: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeywordSettings':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BudgetSettings:
    """Campaign budget settings."""
    daily_budget: float = 500.00
    target_cpa: float = 75.00
    max_cpc_limit: float = 100.00
    budget_delivery: str = "standard"  # standard or accelerated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BudgetSettings':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ProjectConfig:
    """Main project configuration."""
    
    project_name: str = ""
    target_platforms: List[str] = field(default_factory=lambda: ["google_ads"])
    target_locations: LocationSettings = field(default_factory=LocationSettings)
    keyword_settings: KeywordSettings = field(default_factory=KeywordSettings)
    budget_settings: BudgetSettings = field(default_factory=BudgetSettings)
    language: str = "en"
    currency: str = "USD"
    country_code: str = "US"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "project_name": self.project_name,
            "target_platforms": self.target_platforms,
            "target_locations": self.target_locations.to_dict(),
            "keyword_settings": self.keyword_settings.to_dict(),
            "budget_settings": self.budget_settings.to_dict(),
            "language": self.language,
            "currency": self.currency,
            "country_code": self.country_code
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectConfig':
        """Create from dictionary."""
        config = cls()
        config.project_name = data.get("project_name", "")
        config.target_platforms = data.get("target_platforms", ["google_ads"])
        config.target_locations = LocationSettings.from_dict(
            data.get("target_locations", {})
        )
        config.keyword_settings = KeywordSettings.from_dict(
            data.get("keyword_settings", {})
        )
        config.budget_settings = BudgetSettings.from_dict(
            data.get("budget_settings", {})
        )
        config.language = data.get("language", "en")
        config.currency = data.get("currency", "USD")
        config.country_code = data.get("country_code", "US")
        return config
    
    def save(self, filepath: Path):
        """Save configuration to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'ProjectConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_hash(self) -> str:
        """Generate hash of configuration for change detection."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate project name
        if not self.project_name:
            errors.append("Project name cannot be empty")
        
        # Validate platforms
        valid_platforms = ["google_ads", "bing_ads"]
        for platform in self.target_platforms:
            if platform not in valid_platforms:
                errors.append(f"Invalid platform: {platform}")
        
        if not self.target_platforms:
            errors.append("At least one target platform must be specified")
        
        # Validate location settings
        valid_location_types = ["cities", "zipcodes", "both"]
        if self.target_locations.type not in valid_location_types:
            errors.append(f"Invalid location type: {self.target_locations.type}")
        
        if self.target_locations.radius_miles < 0:
            errors.append("Radius must be positive")
        
        # Validate keyword settings
        valid_match_types = ["exact", "phrase", "broad", "broad_modifier"]
        for match_type in self.keyword_settings.match_types:
            if match_type not in valid_match_types:
                errors.append(f"Invalid match type: {match_type}")
        
        if self.keyword_settings.min_search_volume < 0:
            errors.append("Minimum search volume must be non-negative")
        
        if self.keyword_settings.max_cpc <= 0:
            errors.append("Maximum CPC must be positive")
        
        # Validate budget settings
        if self.budget_settings.daily_budget <= 0:
            errors.append("Daily budget must be positive")
        
        if self.budget_settings.target_cpa <= 0:
            errors.append("Target CPA must be positive")
        
        valid_delivery = ["standard", "accelerated"]
        if self.budget_settings.budget_delivery not in valid_delivery:
            errors.append(f"Invalid budget delivery: {self.budget_settings.budget_delivery}")
        
        return len(errors) == 0, errors


@dataclass
class CampaignSettings:
    """Campaign-specific settings."""
    
    campaign_type: str = "search"
    bidding_strategy: str = "maximize_conversions"
    ad_rotation: str = "optimize"
    delivery_method: str = "standard"
    networks: Dict[str, bool] = field(default_factory=lambda: {
        "search": True,
        "search_partners": False,
        "display": False
    })
    scheduling: Dict[str, Any] = field(default_factory=lambda: {
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "end_date": None,
        "ad_schedule": []
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CampaignSettings':
        """Create from dictionary."""
        return cls(**data)
    
    def save(self, filepath: Path):
        """Save settings to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'CampaignSettings':
        """Load settings from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class ProcessingRules:
    """Keyword processing rules."""
    
    remove_duplicates: bool = True
    remove_brand_terms: bool = False
    brand_terms: List[str] = field(default_factory=list)
    min_word_count: int = 1
    max_word_count: int = 10
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    negative_generation_rules: Dict[str, Any] = field(default_factory=lambda: {
        "auto_generate": True,
        "include_competitors": True,
        "include_irrelevant_terms": True,
        "custom_rules": []
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingRules':
        """Create from dictionary."""
        return cls(**data)
    
    def save(self, filepath: Path):
        """Save rules to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'ProcessingRules':
        """Load rules from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_default_configs(project_path: Path, project_name: str):
    """
    Create default configuration files for a new project.
    
    Args:
        project_path: Path to the project directory
        project_name: Name of the project
    """
    configs_path = project_path / "configs"
    configs_path.mkdir(exist_ok=True)
    
    # Create main project config
    project_config = ProjectConfig(project_name=project_name)
    project_config.save(configs_path / "project_config.json")
    
    # Create campaign settings
    campaign_settings = CampaignSettings()
    campaign_settings.save(configs_path / "campaign_settings.json")
    
    # Create processing rules
    processing_rules = ProcessingRules()
    processing_rules.save(configs_path / "processing_rules.json")
    
    # Create API config template (without actual keys)
    api_config = {
        "dataforseo": {
            "enabled": True,
            "api_key_env": "DATAFORSEO_API_KEY",
            "max_retries": 3,
            "timeout": 60
        },
        "serper": {
            "enabled": False,
            "api_key_env": "SERPER_API_KEY",
            "max_retries": 3,
            "timeout": 30
        },
        "firecrawl": {
            "enabled": False,
            "api_key_env": "FIRECRAWL_API_KEY",
            "max_retries": 3,
            "timeout": 120
        }
    }
    
    with open(configs_path / "api_config.json", 'w') as f:
        json.dump(api_config, f, indent=2)
    
    # Create templates directory
    templates_path = configs_path / "templates"
    templates_path.mkdir(exist_ok=True)
    
    # Create ad group template
    ad_group_template = {
        "naming_pattern": "{service} - {location}",
        "max_keywords_per_group": 20,
        "group_by": ["service", "location"],
        "include_modifiers": True
    }
    
    with open(templates_path / "ad_group_template.json", 'w') as f:
        json.dump(ad_group_template, f, indent=2)
    
    # Create output format template
    output_format = {
        "csv_delimiter": ",",
        "csv_encoding": "utf-8",
        "include_headers": True,
        "google_ads_format": True,
        "bing_ads_format": False,
        "include_metrics": True
    }
    
    with open(templates_path / "output_format.json", 'w') as f:
        json.dump(output_format, f, indent=2)