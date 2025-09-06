"""
Project Structure Definition

Defines the standardized folder structure for campaign projects.
"""

from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import uuid


@dataclass
class ProjectStructure:
    """Defines the complete project folder structure."""
    
    # Main directories
    INPUTS_DIR = "inputs"
    CONFIGS_DIR = "configs"
    OUTPUTS_DIR = "outputs"
    CACHE_DIR = "cache"
    LOGS_DIR = "logs"
    
    # Input subdirectories
    KEYWORDS_DIR = "keywords"
    LOCATIONS_DIR = "locations"
    CATEGORIES_DIR = "categories"
    COMPETITORS_DIR = "competitors"
    CUSTOM_DIR = "custom"
    
    # Output subdirectories
    OUTPUT_KEYWORDS_DIR = "keywords"
    AD_GROUPS_DIR = "ad_groups"
    NEGATIVES_DIR = "negatives"
    ANALYSIS_DIR = "analysis"
    EXPORTS_DIR = "exports"
    REPORTS_DIR = "reports"
    
    # Cache subdirectories
    CACHE_DATAFORSEO = "dataforseo"
    CACHE_SERPER = "serper"
    CACHE_FIRECRAWL = "firecrawl"
    
    # Config subdirectory
    TEMPLATES_DIR = "templates"
    
    @classmethod
    def get_structure_definition(cls) -> Dict[str, Any]:
        """Returns the complete project structure definition."""
        return PROJECT_STRUCTURE_DEFINITION


# Complete project structure definition
PROJECT_STRUCTURE_DEFINITION = {
    "inputs": {
        "keywords": {
            "files": [
                "seed_keywords.txt",
                "seed_keywords.csv",
                "negative_keywords.txt"
            ]
        },
        "locations": {
            "files": [
                "cities.csv",
                "zipcodes.csv",
                "locations_combined.csv"
            ]
        },
        "categories": {
            "files": [
                "services.csv",
                "categories.txt",
                "category_mappings.json"
            ]
        },
        "competitors": {
            "files": [
                "competitor_urls.txt",
                "spyfu_export.csv",
                "competitor_keywords.csv"
            ]
        },
        "custom": {
            "files": []
        }
    },
    "configs": {
        "files": [
            "project_config.json",
            "api_config.json",
            "campaign_settings.json",
            "processing_rules.json"
        ],
        "templates": {
            "files": [
                "ad_group_template.json",
                "output_format.json"
            ]
        }
    },
    "outputs": {
        "keywords": {
            "files": [
                "expanded_keywords.csv",
                "categorized_keywords.csv",
                "final_keywords.csv"
            ]
        },
        "ad_groups": {
            "files": [
                "ad_groups_by_location.csv",
                "ad_groups_by_service.csv",
                "ad_groups_combined.csv"
            ]
        },
        "negatives": {
            "files": [
                "negative_keywords.csv",
                "negative_lists.csv",
                "shared_negatives.csv"
            ]
        },
        "analysis": {
            "files": [
                "competition_report.csv",
                "keyword_gaps.csv",
                "landing_page_insights.csv",
                "performance_predictions.csv"
            ]
        },
        "exports": {
            "files": [
                "google_ads_import.csv",
                "bing_ads_import.csv",
                "campaign_export.zip"
            ]
        },
        "reports": {
            "files": [
                "campaign_summary.txt",
                "statistics.json",
                "generation_report.html"
            ]
        }
    },
    "cache": {
        "dataforseo": {
            "search_volume": {},
            "keyword_suggestions": {},
            "competitor_analysis": {}
        },
        "serper": {},
        "firecrawl": {}
    },
    "logs": {
        "files": [
            "api_calls.log",
            "processing.log",
            "errors.log",
            "audit.log"
        ]
    }
}


@dataclass
class ProjectMetadata:
    """Project metadata structure."""
    
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    created_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_modified: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0.0"
    parent_project: str = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    status: str = "active"
    statistics: Dict[str, Any] = field(default_factory=lambda: {
        "total_keywords": 0,
        "total_ad_groups": 0,
        "total_locations": 0,
        "api_calls_made": 0,
        "last_generation_date": None
    })
    configuration_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "created_date": self.created_date,
            "last_modified": self.last_modified,
            "version": self.version,
            "parent_project": self.parent_project,
            "description": self.description,
            "tags": self.tags,
            "status": self.status,
            "statistics": self.statistics,
            "configuration_hash": self.configuration_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """Create metadata from dictionary."""
        return cls(**data)
    
    def save(self, filepath: Path):
        """Save metadata to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filepath: Path) -> 'ProjectMetadata':
        """Load metadata from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_project_structure(project_path: Path, include_samples: bool = False) -> Dict[str, Path]:
    """
    Create the complete project folder structure.
    
    Args:
        project_path: Path to the project directory
        include_samples: Whether to create sample files
    
    Returns:
        Dictionary mapping structure names to their paths
    """
    paths = {}
    
    # Create main project directory
    project_path.mkdir(parents=True, exist_ok=True)
    paths['root'] = project_path
    
    # Create main directories
    for main_dir in [ProjectStructure.INPUTS_DIR, ProjectStructure.CONFIGS_DIR, 
                     ProjectStructure.OUTPUTS_DIR, ProjectStructure.CACHE_DIR, 
                     ProjectStructure.LOGS_DIR]:
        dir_path = project_path / main_dir
        dir_path.mkdir(exist_ok=True)
        paths[main_dir] = dir_path
    
    # Create input subdirectories
    inputs_path = project_path / ProjectStructure.INPUTS_DIR
    for sub_dir in [ProjectStructure.KEYWORDS_DIR, ProjectStructure.LOCATIONS_DIR,
                    ProjectStructure.CATEGORIES_DIR, ProjectStructure.COMPETITORS_DIR,
                    ProjectStructure.CUSTOM_DIR]:
        sub_path = inputs_path / sub_dir
        sub_path.mkdir(exist_ok=True)
        paths[f"inputs_{sub_dir}"] = sub_path
    
    # Create output subdirectories
    outputs_path = project_path / ProjectStructure.OUTPUTS_DIR
    for sub_dir in [ProjectStructure.OUTPUT_KEYWORDS_DIR, ProjectStructure.AD_GROUPS_DIR,
                    ProjectStructure.NEGATIVES_DIR, ProjectStructure.ANALYSIS_DIR,
                    ProjectStructure.EXPORTS_DIR, ProjectStructure.REPORTS_DIR]:
        sub_path = outputs_path / sub_dir
        sub_path.mkdir(exist_ok=True)
        paths[f"outputs_{sub_dir}"] = sub_path
    
    # Create cache subdirectories
    cache_path = project_path / ProjectStructure.CACHE_DIR
    for provider in [ProjectStructure.CACHE_DATAFORSEO, ProjectStructure.CACHE_SERPER,
                     ProjectStructure.CACHE_FIRECRAWL]:
        provider_path = cache_path / provider
        provider_path.mkdir(exist_ok=True)
        paths[f"cache_{provider}"] = provider_path
        
        # Create DataForSEO subdirectories
        if provider == ProjectStructure.CACHE_DATAFORSEO:
            for sub_cache in ["search_volume", "keyword_suggestions", "competitor_analysis"]:
                sub_cache_path = provider_path / sub_cache
                sub_cache_path.mkdir(exist_ok=True)
                paths[f"cache_{provider}_{sub_cache}"] = sub_cache_path
    
    # Create config templates directory
    templates_path = project_path / ProjectStructure.CONFIGS_DIR / ProjectStructure.TEMPLATES_DIR
    templates_path.mkdir(exist_ok=True)
    paths['config_templates'] = templates_path
    
    # Create .gitkeep files in empty directories
    for path in paths.values():
        if path.is_dir() and not any(path.iterdir()):
            gitkeep = path / ".gitkeep"
            gitkeep.touch()
    
    return paths


def validate_project_structure(project_path: Path) -> tuple[bool, List[str]]:
    """
    Validate that a project has the correct structure.
    
    Args:
        project_path: Path to the project directory
    
    Returns:
        Tuple of (is_valid, list_of_missing_items)
    """
    missing = []
    
    if not project_path.exists():
        return False, [f"Project directory does not exist: {project_path}"]
    
    # Check main directories
    for main_dir in [ProjectStructure.INPUTS_DIR, ProjectStructure.CONFIGS_DIR,
                     ProjectStructure.OUTPUTS_DIR, ProjectStructure.CACHE_DIR,
                     ProjectStructure.LOGS_DIR]:
        dir_path = project_path / main_dir
        if not dir_path.exists():
            missing.append(f"Missing directory: {main_dir}/")
    
    # Check metadata file
    metadata_path = project_path / "metadata.json"
    if not metadata_path.exists():
        missing.append("Missing metadata.json file")
    
    return len(missing) == 0, missing