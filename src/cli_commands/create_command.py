"""Implementation of the 'create' CLI command."""

import logging
from pathlib import Path
from typing import Optional

from src.project_manager.project_manager import ProjectManager
from src.project_manager.project_config import (
    ProjectConfig,
    LocationSettings,
    KeywordSettings,
    BudgetSettings
)

logger = logging.getLogger(__name__)


def execute_create(args, project_manager: ProjectManager) -> int:
    """
    Execute the create command to initialize a new project.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        project_name = args.project_name
        
        # Check if project already exists
        if project_manager.get_project_path(project_name):
            logger.error(f"Project '{project_name}' already exists")
            return 1
        
        # Create configuration based on arguments
        config = None
        
        if args.interactive:
            # Interactive mode - prompt for configuration
            config = create_interactive_config(project_name)
        else:
            # Create config from arguments
            config = create_config_from_args(args, project_name)
        
        # Create project
        if args.template:
            # Create from template
            template_path = project_manager.get_project_path(args.template)
            if not template_path:
                logger.error(f"Template project '{args.template}' not found")
                return 1
            
            logger.info(f"Creating project '{project_name}' from template '{args.template}'")
            project_path = project_manager.create_project(
                project_name,
                template=args.template,
                config=config
            )
        else:
            # Create new project
            logger.info(f"Creating new project '{project_name}'")
            project_path = project_manager.create_project(
                project_name,
                config=config
            )
        
        # Create industry-specific templates if specified
        if args.industry != 'general':
            create_industry_templates(project_path, args.industry)
        
        logger.info(f"✓ Project '{project_name}' created successfully at {project_path}")
        print(f"\nProject created at: {project_path}")
        print("\nNext steps:")
        print(f"1. Add seed keywords to: {project_path}/inputs/keywords/seed_keywords.txt")
        print(f"2. Add locations to: {project_path}/inputs/locations/cities.csv")
        print(f"3. Run keyword research: ppc research --project {project_name}")
        print(f"4. Generate ad groups: ppc generate --project {project_name}")
        print(f"5. Export campaign: ppc export --project {project_name}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        return 1


def create_config_from_args(args, project_name: str) -> ProjectConfig:
    """
    Create project configuration from command line arguments.
    
    Args:
        args: Command line arguments
        project_name: Name of the project
        
    Returns:
        ProjectConfig instance
    """
    # Determine target platforms
    platforms = []
    if 'google' in args.platforms or 'both' in args.platforms:
        platforms.append('google_ads')
    if 'bing' in args.platforms or 'both' in args.platforms:
        platforms.append('bing_ads')
    
    # Set industry-specific defaults
    industry_defaults = get_industry_defaults(args.industry)
    
    config = ProjectConfig(
        project_name=project_name,
        target_platforms=platforms,
        target_locations=LocationSettings(
            type="cities",
            include_surrounding=True,
            radius_miles=industry_defaults['radius']
        ),
        keyword_settings=KeywordSettings(
            match_types=["exact", "phrase", "broad"],
            include_variations=True,
            min_search_volume=industry_defaults['min_volume'],
            max_cpc=industry_defaults['max_cpc'],
            include_questions=True,
            include_long_tail=True
        ),
        budget_settings=BudgetSettings(
            daily_budget=industry_defaults['daily_budget'],
            target_cpa=industry_defaults['target_cpa'],
            max_cpc_limit=industry_defaults['max_cpc']
        ),
        language="en",
        currency="USD",
        country_code="US"
    )
    
    return config


def create_interactive_config(project_name: str) -> ProjectConfig:
    """
    Create project configuration through interactive prompts.
    
    Args:
        project_name: Name of the project
        
    Returns:
        ProjectConfig instance
    """
    print("\n=== Project Configuration ===\n")
    
    # Platform selection
    print("Select target platforms:")
    print("1. Google Ads only")
    print("2. Bing Ads only")
    print("3. Both Google and Bing")
    platform_choice = input("Enter choice (1-3) [3]: ").strip() or "3"
    
    platforms = []
    if platform_choice in ["1", "3"]:
        platforms.append("google_ads")
    if platform_choice in ["2", "3"]:
        platforms.append("bing_ads")
    
    # Location settings
    print("\nLocation targeting:")
    radius = input("Radius in miles for location targeting [25]: ").strip()
    radius = int(radius) if radius else 25
    
    # Budget settings
    print("\nBudget configuration:")
    daily_budget = input("Daily budget in USD [500]: ").strip()
    daily_budget = float(daily_budget) if daily_budget else 500.0
    
    target_cpa = input("Target CPA in USD [75]: ").strip()
    target_cpa = float(target_cpa) if target_cpa else 75.0
    
    max_cpc = input("Maximum CPC in USD [50]: ").strip()
    max_cpc = float(max_cpc) if max_cpc else 50.0
    
    # Keyword settings
    print("\nKeyword settings:")
    min_volume = input("Minimum search volume [10]: ").strip()
    min_volume = int(min_volume) if min_volume else 10
    
    config = ProjectConfig(
        project_name=project_name,
        target_platforms=platforms,
        target_locations=LocationSettings(
            type="cities",
            include_surrounding=True,
            radius_miles=radius
        ),
        keyword_settings=KeywordSettings(
            match_types=["exact", "phrase", "broad"],
            include_variations=True,
            min_search_volume=min_volume,
            max_cpc=max_cpc,
            include_questions=True,
            include_long_tail=True
        ),
        budget_settings=BudgetSettings(
            daily_budget=daily_budget,
            target_cpa=target_cpa,
            max_cpc_limit=max_cpc
        ),
        language="en",
        currency="USD",
        country_code="US"
    )
    
    return config


def get_industry_defaults(industry: str) -> dict:
    """
    Get default settings for specific industries.
    
    Args:
        industry: Industry type
        
    Returns:
        Dictionary of default settings
    """
    defaults = {
        'plumbing': {
            'radius': 30,
            'min_volume': 10,
            'max_cpc': 75.0,
            'daily_budget': 500.0,
            'target_cpa': 100.0,
            'categories': ['emergency', 'repair', 'installation', 'maintenance'],
            'negative_keywords': ['diy', 'free', 'tutorial', 'how to', 'jobs', 'salary']
        },
        'hvac': {
            'radius': 35,
            'min_volume': 20,
            'max_cpc': 80.0,
            'daily_budget': 600.0,
            'target_cpa': 120.0,
            'categories': ['heating', 'cooling', 'repair', 'installation', 'maintenance'],
            'negative_keywords': ['diy', 'free', 'manual', 'diagram', 'jobs', 'career']
        },
        'electrical': {
            'radius': 25,
            'min_volume': 15,
            'max_cpc': 60.0,
            'daily_budget': 450.0,
            'target_cpa': 90.0,
            'categories': ['emergency', 'repair', 'installation', 'inspection'],
            'negative_keywords': ['diy', 'free', 'code', 'manual', 'jobs', 'license']
        },
        'roofing': {
            'radius': 40,
            'min_volume': 30,
            'max_cpc': 90.0,
            'daily_budget': 700.0,
            'target_cpa': 150.0,
            'categories': ['repair', 'replacement', 'inspection', 'emergency'],
            'negative_keywords': ['diy', 'free', 'calculator', 'cost', 'jobs', 'salary']
        },
        'general': {
            'radius': 25,
            'min_volume': 10,
            'max_cpc': 50.0,
            'daily_budget': 500.0,
            'target_cpa': 75.0,
            'categories': [],
            'negative_keywords': ['free', 'diy', 'jobs']
        }
    }
    
    return defaults.get(industry, defaults['general'])


def create_industry_templates(project_path: Path, industry: str):
    """
    Create industry-specific template files.
    
    Args:
        project_path: Path to the project
        industry: Industry type
    """
    defaults = get_industry_defaults(industry)
    
    # Create seed keywords file
    keywords_file = project_path / "inputs" / "keywords" / "seed_keywords.txt"
    if industry == 'plumbing':
        keywords_content = """# Plumbing Service Keywords
emergency plumber
24 hour plumber
plumber near me
water heater repair
drain cleaning
pipe repair
leak detection
toilet repair
sewer line repair
plumbing services
"""
    elif industry == 'hvac':
        keywords_content = """# HVAC Service Keywords
ac repair
heating repair
hvac service
air conditioning installation
furnace repair
hvac maintenance
emergency hvac
duct cleaning
thermostat installation
heat pump repair
"""
    elif industry == 'electrical':
        keywords_content = """# Electrical Service Keywords
electrician near me
emergency electrician
electrical repair
circuit breaker repair
outlet installation
electrical inspection
panel upgrade
wiring repair
lighting installation
electrical services
"""
    elif industry == 'roofing':
        keywords_content = """# Roofing Service Keywords
roof repair
roof replacement
roofing contractor
emergency roof repair
roof inspection
shingle repair
roof leak repair
gutter installation
roof maintenance
roofing services
"""
    else:
        return
    
    with open(keywords_file, 'w') as f:
        f.write(keywords_content)
    
    # Create negative keywords file
    neg_keywords_file = project_path / "inputs" / "keywords" / "negative_keywords.txt"
    neg_content = "# Negative Keywords\n"
    neg_content += "\n".join(defaults['negative_keywords'])
    
    with open(neg_keywords_file, 'w') as f:
        f.write(neg_content)
    
    # Create categories file
    if defaults['categories']:
        categories_file = project_path / "inputs" / "categories" / "services.csv"
        categories_content = "service_name,category,priority\n"
        for i, category in enumerate(defaults['categories'], 1):
            categories_content += f'"{category.title()} Services","{category}",{i}\n'
        
        with open(categories_file, 'w') as f:
            f.write(categories_content)
    
    logger.info(f"Created {industry} industry templates")