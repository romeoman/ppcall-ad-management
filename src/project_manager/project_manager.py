"""
Project Manager

Main class for managing PPC campaign projects with isolated folder structures.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import shutil
import json
import logging

from .project_structure import (
    ProjectStructure, 
    PROJECT_STRUCTURE_DEFINITION,
    ProjectMetadata,
    create_project_structure,
    validate_project_structure
)
from .project_config import (
    ProjectConfig,
    CampaignSettings,
    ProcessingRules,
    create_default_configs
)


logger = logging.getLogger(__name__)


class ProjectManager:
    """
    Manages PPC campaign projects with isolated folder structures.
    
    Each project is self-contained with inputs, configurations, and outputs,
    enabling easy replication and management across different campaigns.
    """
    
    def __init__(self, base_path: str = "projects"):
        """
        Initialize the Project Manager.
        
        Args:
            base_path: Base directory for all projects (default: "projects")
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"ProjectManager initialized with base path: {self.base_path}")
    
    def create_project(
        self, 
        project_name: str,
        template: Optional[str] = None,
        config: Optional[ProjectConfig] = None
    ) -> Path:
        """
        Create a new project with the standard folder structure.
        
        Args:
            project_name: Name of the project (used as folder name)
            template: Optional template project to copy from
            config: Optional ProjectConfig to use (creates default if None)
            
        Returns:
            Path to the created project directory
            
        Raises:
            ValueError: If project already exists
            FileNotFoundError: If template project doesn't exist
        """
        project_path = self.base_path / project_name
        
        if project_path.exists():
            raise ValueError(f"Project '{project_name}' already exists at {project_path}")
        
        if template:
            # Clone from template
            template_path = self.base_path / template
            if not template_path.exists():
                raise FileNotFoundError(f"Template project '{template}' not found")
            
            logger.info(f"Creating project '{project_name}' from template '{template}'")
            project_path = self._clone_project_internal(template_path, project_path, project_name)
        else:
            # Create new project structure
            logger.info(f"Creating new project '{project_name}'")
            paths = create_project_structure(project_path, include_samples=False)
            
            # Create metadata
            metadata = ProjectMetadata(
                project_name=project_name,
                description=f"PPC campaign project: {project_name}",
                status="active"
            )
            metadata.save(project_path / "metadata.json")
            
            # Create default configurations
            create_default_configs(project_path, project_name)
            
            # If custom config provided, merge with defaults
            if config:
                config_path = project_path / "configs" / "project_config.json"
                default_config = ProjectConfig.load(config_path)
                
                # Update with provided config values
                if config.project_name:
                    default_config.project_name = config.project_name
                if config.target_platforms:
                    default_config.target_platforms = config.target_platforms
                if config.target_locations:
                    default_config.target_locations = config.target_locations
                if config.keyword_settings:
                    default_config.keyword_settings = config.keyword_settings
                if config.budget_settings:
                    default_config.budget_settings = config.budget_settings
                if config.language:
                    default_config.language = config.language
                if config.currency:
                    default_config.currency = config.currency
                if config.country_code:
                    default_config.country_code = config.country_code
                
                default_config.save(config_path)
            
            # Create README
            self._create_project_readme(project_path, project_name)
            
            # Create sample input files
            self._create_sample_inputs(project_path)
        
        logger.info(f"Project '{project_name}' created successfully at {project_path}")
        return project_path
    
    def validate_project(self, project_name: str) -> tuple[bool, List[str]]:
        """
        Validate that a project has the correct structure.
        
        Args:
            project_name: Name of the project to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        project_path = self.base_path / project_name
        return validate_project_structure(project_path)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects with their metadata.
        
        Returns:
            List of project information dictionaries
        """
        projects = []
        
        for project_dir in self.base_path.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                try:
                    metadata_path = project_dir / "metadata.json"
                    if metadata_path.exists():
                        metadata = ProjectMetadata.load(metadata_path)
                        
                        # Add validation status
                        is_valid, issues = self.validate_project(project_dir.name)
                        
                        project_info = metadata.to_dict()
                        project_info["path"] = str(project_dir)
                        project_info["is_valid"] = is_valid
                        project_info["validation_issues"] = issues
                        
                        projects.append(project_info)
                except Exception as e:
                    logger.warning(f"Error reading project {project_dir.name}: {e}")
                    projects.append({
                        "project_name": project_dir.name,
                        "path": str(project_dir),
                        "error": str(e),
                        "is_valid": False
                    })
        
        return sorted(projects, key=lambda x: x.get("created_date", ""))
    
    def get_project_path(self, project_name: str) -> Optional[Path]:
        """
        Get the path to a project directory.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to project directory or None if not found
        """
        project_path = self.base_path / project_name
        return project_path if project_path.exists() else None
    
    def clone_project(
        self, 
        source_project: str, 
        target_project: str,
        clear_outputs: bool = True,
        clear_cache: bool = True
    ) -> Path:
        """
        Clone an existing project to create a new campaign.
        
        Args:
            source_project: Name of the source project
            target_project: Name of the new project
            clear_outputs: Whether to clear output directories
            clear_cache: Whether to clear cache directories
            
        Returns:
            Path to the cloned project
            
        Raises:
            FileNotFoundError: If source project doesn't exist
            ValueError: If target project already exists
        """
        source_path = self.base_path / source_project
        if not source_path.exists():
            raise FileNotFoundError(f"Source project '{source_project}' not found")
        
        target_path = self.base_path / target_project
        if target_path.exists():
            raise ValueError(f"Target project '{target_project}' already exists")
        
        logger.info(f"Cloning project '{source_project}' to '{target_project}'")
        
        cloned_path = self._clone_project_internal(
            source_path, target_path, target_project,
            clear_outputs=clear_outputs,
            clear_cache=clear_cache
        )
        
        logger.info(f"Project cloned successfully to {cloned_path}")
        return cloned_path
    
    def _clone_project_internal(
        self,
        source_path: Path,
        target_path: Path,
        new_name: str,
        clear_outputs: bool = True,
        clear_cache: bool = True
    ) -> Path:
        """
        Internal method to handle project cloning.
        
        Args:
            source_path: Source project path
            target_path: Target project path
            new_name: New project name
            clear_outputs: Whether to clear outputs
            clear_cache: Whether to clear cache
            
        Returns:
            Path to cloned project
        """
        # Copy entire project directory
        shutil.copytree(source_path, target_path)
        
        # Update metadata
        metadata_path = target_path / "metadata.json"
        if metadata_path.exists():
            metadata = ProjectMetadata.load(metadata_path)
            metadata.project_name = new_name
            metadata.parent_project = metadata.project_id
            metadata.project_id = str(datetime.now().timestamp())
            metadata.created_date = datetime.now(timezone.utc).isoformat()
            metadata.status = "active"
            metadata.save(metadata_path)
        
        # Update project config
        config_path = target_path / "configs" / "project_config.json"
        if config_path.exists():
            config = ProjectConfig.load(config_path)
            config.project_name = new_name
            config.save(config_path)
        
        # Clear outputs if requested
        if clear_outputs:
            outputs_path = target_path / "outputs"
            if outputs_path.exists():
                for subdir in outputs_path.iterdir():
                    if subdir.is_dir():
                        for file in subdir.iterdir():
                            if file.is_file() and not file.name == ".gitkeep":
                                file.unlink()
        
        # Clear cache if requested
        if clear_cache:
            cache_path = target_path / "cache"
            if cache_path.exists():
                for subdir in cache_path.iterdir():
                    if subdir.is_dir():
                        for file in subdir.rglob("*"):
                            if file.is_file() and not file.name == ".gitkeep":
                                file.unlink()
        
        # Clear logs
        logs_path = target_path / "logs"
        if logs_path.exists():
            for file in logs_path.iterdir():
                if file.is_file() and file.suffix == ".log":
                    file.unlink()
        
        return target_path
    
    def delete_project(self, project_name: str, confirm: bool = False) -> bool:
        """
        Delete a project and all its contents.
        
        Args:
            project_name: Name of the project to delete
            confirm: Safety confirmation flag
            
        Returns:
            True if deleted, False otherwise
        """
        if not confirm:
            logger.warning("Project deletion requires confirmation flag")
            return False
        
        project_path = self.base_path / project_name
        if not project_path.exists():
            logger.error(f"Project '{project_name}' not found")
            return False
        
        try:
            shutil.rmtree(project_path)
            logger.info(f"Project '{project_name}' deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project '{project_name}': {e}")
            return False
    
    def archive_project(self, project_name: str, archive_path: Optional[Path] = None) -> Path:
        """
        Archive a project to a zip file.
        
        Args:
            project_name: Name of the project to archive
            archive_path: Optional path for the archive (defaults to archives/ directory)
            
        Returns:
            Path to the created archive
        """
        project_path = self.base_path / project_name
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found")
        
        if archive_path is None:
            archives_dir = self.base_path / "archives"
            archives_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_path = archives_dir / f"{project_name}_{timestamp}.zip"
        
        logger.info(f"Archiving project '{project_name}' to {archive_path}")
        
        # Create zip archive
        shutil.make_archive(
            str(archive_path.with_suffix('')),
            'zip',
            project_path.parent,
            project_path.name
        )
        
        logger.info(f"Project archived successfully to {archive_path}")
        return archive_path
    
    def _create_project_readme(self, project_path: Path, project_name: str):
        """
        Create a README file for the project.
        
        Args:
            project_path: Path to project directory
            project_name: Name of the project
        """
        readme_content = f"""# {project_name} - PPC Campaign Project

## Project Structure

```
{project_name}/
├── inputs/           # Input data for the campaign
│   ├── keywords/     # Seed and negative keywords
│   ├── locations/    # Geographic targeting data
│   ├── categories/   # Service categories and themes
│   ├── competitors/  # Competitor analysis data
│   └── custom/       # Custom input files
├── configs/          # Configuration files
│   ├── project_config.json      # Main project settings
│   ├── api_config.json          # API configurations
│   ├── campaign_settings.json   # Campaign parameters
│   ├── processing_rules.json    # Processing rules
│   └── templates/               # Reusable templates
├── outputs/          # Generated outputs
│   ├── keywords/     # Generated keywords
│   ├── ad_groups/    # Ad group structures
│   ├── negatives/    # Negative keywords
│   ├── analysis/     # Analysis reports
│   ├── exports/      # Platform-ready exports
│   └── reports/      # Summary reports
├── cache/            # API response cache
└── logs/             # Processing logs
```

## Usage

1. **Add Input Data**: Place your seed keywords, locations, and other inputs in the `inputs/` directory
2. **Configure Settings**: Edit configuration files in `configs/` to match your campaign requirements
3. **Run Processing**: Use the PPC Campaign Manager to process inputs and generate outputs
4. **Review Outputs**: Check the `outputs/` directory for generated keywords, ad groups, and reports

## Configuration

- `project_config.json`: Main project settings including platform targeting and budget
- `api_config.json`: API keys and rate limiting settings
- `campaign_settings.json`: Campaign-specific parameters
- `processing_rules.json`: Keyword processing and filtering rules

## Notes

Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        readme_path = project_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    def _create_sample_inputs(self, project_path: Path):
        """
        Create sample input files for a new project.
        
        Args:
            project_path: Path to project directory
        """
        # Sample seed keywords
        keywords_path = project_path / "inputs" / "keywords"
        
        seed_keywords = """# Seed Keywords - One per line
# Add your initial keywords here
# Example:
plumbing services
emergency plumber
water heater repair
drain cleaning
pipe repair
"""
        with open(keywords_path / "seed_keywords.txt", 'w') as f:
            f.write(seed_keywords)
        
        negative_keywords = """# Negative Keywords - One per line
# Add keywords to exclude from your campaigns
# Example:
free
diy
tutorial
how to
cheap
"""
        with open(keywords_path / "negative_keywords.txt", 'w') as f:
            f.write(negative_keywords)
        
        # Sample locations CSV
        locations_path = project_path / "inputs" / "locations"
        cities_csv = """city,state,population
# Add your target cities here
# Example:
"New York","NY",8336817
"Los Angeles","CA",3979576
"Chicago","IL",2693976
"Houston","TX",2320268
"Phoenix","AZ",1680992
"""
        with open(locations_path / "cities.csv", 'w') as f:
            f.write(cities_csv)
        
        # Sample categories
        categories_path = project_path / "inputs" / "categories"
        services_csv = """service_name,category,priority
# Define your service categories
# Example:
"Emergency Services","emergency",1
"Installation","installation",2
"Repair Services","repair",2
"Maintenance","maintenance",3
"Inspection","inspection",3
"""
        with open(categories_path / "services.csv", 'w') as f:
            f.write(services_csv)