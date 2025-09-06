"""
PPC Keyword Automator - Main CLI Entry Point

This module integrates all components to provide a command-line interface
for automating PPC keyword generation and campaign creation.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from src.input_parser.parsers import InputParser
from src.api_integration.dataforseo_client import DataForSEOClient
from src.api_integration.serper_client import SerperClient
from src.api_integration.firecrawl_client import FireCrawlClient
from src.processors.keyword_processor import KeywordProcessor
from src.processors.ad_group_processor import AdGroupProcessor
from src.processors.landing_page_scraper import LandingPageScraper
from src.output_generator.csv_exporter import CSVExporter
from src.project_manager.project_manager import ProjectManager
from models.keyword_models import NegativeKeyword


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "ppc_automator.log"),
            logging.StreamHandler()
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PPC Keyword Automator - Automate PPC campaign creation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic keyword expansion
  python main.py --project my_campaign --seeds data/input/seed_keywords.txt --locations data/input/locations.csv
  
  # Full processing with competition analysis
  python main.py --project my_campaign --seeds seeds.txt --locations locations.csv --spyfu competition.csv --urls competitor_urls.txt
  
  # Export to specific directory
  python main.py --project my_campaign --seeds seeds.txt --locations locations.csv --output exports/
        """
    )
    
    # Project arguments
    parser.add_argument('--project', required=True, 
                       help='Project name or path to existing project')
    parser.add_argument('--create', action='store_true',
                       help='Create new project if it does not exist')
    
    # Input files
    parser.add_argument('--seeds', 
                       help='Path to seed keywords file (CSV or TXT)')
    parser.add_argument('--categories', 
                       help='Path to categories file (CSV)')
    parser.add_argument('--locations', 
                       help='Path to locations file (CSV)')
    parser.add_argument('--negative-keywords',
                       help='Path to negative keywords file (TXT)')
    parser.add_argument('--spyfu', 
                       help='Path to SpyFu competition data (CSV)')
    parser.add_argument('--urls', 
                       help='Path to competitor URLs file (TXT)')
    
    # Processing options
    parser.add_argument('--match-types', nargs='+', 
                       default=['broad', 'phrase', 'exact'],
                       choices=['broad', 'phrase', 'exact'],
                       help='Match types for ad groups (default: all)')
    parser.add_argument('--max-keywords', type=int, default=1000,
                       help='Maximum keywords to generate (default: 1000)')
    parser.add_argument('--min-volume', type=int, default=10,
                       help='Minimum search volume filter (default: 10)')
    parser.add_argument('--max-cpc', type=float, default=50.0,
                       help='Maximum CPC filter (default: 50.0)')
    
    # Output options
    parser.add_argument('--output', default='data/output',
                       help='Output directory for CSV files')
    parser.add_argument('--export-google', action='store_true',
                       help='Export in Google Ads Editor format')
    parser.add_argument('--export-bing', action='store_true',
                       help='Export in Bing Ads format')
    
    # Other options
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without API calls')
    
    return parser.parse_args()


async def process_keywords(args, project_path: Path):
    """
    Main processing pipeline for keywords.
    
    Args:
        args: Command line arguments
        project_path: Path to project directory
    """
    # Initialize components
    input_parser = InputParser()
    csv_exporter = CSVExporter(args.output)
    
    # Initialize API clients if not in dry run
    dataforseo_client = None
    serper_client = None
    firecrawl_client = None
    
    if not args.dry_run:
        dataforseo_client = DataForSEOClient(os.getenv('DATAFORSEO_LOGIN'), os.getenv('DATAFORSEO_PASSWORD'))
        serper_api_key = os.getenv('SERPER_API_KEY')
        if serper_api_key:
            serper_client = SerperClient(serper_api_key)
        firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
        if firecrawl_api_key:
            firecrawl_client = FireCrawlClient(firecrawl_api_key)
    
    # Initialize processors
    keyword_processor = KeywordProcessor(dataforseo_client)
    ad_group_processor = AdGroupProcessor()
    landing_page_scraper = LandingPageScraper(firecrawl_client) if firecrawl_client else None
    
    # Parse inputs
    seed_keywords = []
    locations = []
    categories = []
    negative_keywords = []
    
    if args.seeds:
        seed_keywords = input_parser.parse_seed_keywords(args.seeds)
        logging.info(f"Loaded {len(seed_keywords)} seed keywords")
    
    if args.locations:
        locations = input_parser.parse_locations(args.locations)
        logging.info(f"Loaded {len(locations)} locations")
    
    if args.categories:
        categories = input_parser.parse_categories(args.categories)
        logging.info(f"Loaded {len(categories)} categories")
    
    if args.negative_keywords:
        neg_kw_list = input_parser.parse_negative_keywords(args.negative_keywords)
        negative_keywords = [NegativeKeyword(term=kw) for kw in neg_kw_list]
        logging.info(f"Loaded {len(negative_keywords)} negative keywords")
    
    # Process keywords
    expanded_keywords = []
    
    if seed_keywords and not args.dry_run:
        logging.info("Expanding seed keywords...")
        expanded_keywords = await keyword_processor.expand_seed_keywords(
            seed_keywords,
            categories=categories if categories else None
        )
        
        if locations:
            logging.info("Combining keywords with locations...")
            expanded_keywords = keyword_processor.combine_with_locations(
                expanded_keywords, 
                locations
            )
        
        logging.info(f"Filtering keywords (min_volume={args.min_volume}, max_cpc={args.max_cpc})...")
        expanded_keywords = keyword_processor.filter_keywords(
            expanded_keywords,
            min_volume=args.min_volume,
            max_cpc=args.max_cpc
        )
        
        # Limit keywords if specified
        if len(expanded_keywords) > args.max_keywords:
            expanded_keywords = expanded_keywords[:args.max_keywords]
            logging.info(f"Limited to {args.max_keywords} keywords")
        
        logging.info(f"Generated {len(expanded_keywords)} keywords")
    
    # Generate negative keywords if needed
    if categories and not negative_keywords:
        logging.info("Generating category-based negative keywords...")
        # Generate some default negatives based on categories
        default_negatives = [
            "free", "diy", "cheap", "tutorial", "how to",
            "jobs", "salary", "career", "training", "course"
        ]
        negative_keywords = [NegativeKeyword(term=term, reason="Default exclusion") 
                           for term in default_negatives]
    
    # Create ad groups
    ad_groups = []
    if expanded_keywords:
        logging.info(f"Creating ad groups with match types: {args.match_types}")
        ad_groups = ad_group_processor.create_ad_groups(
            expanded_keywords,
            match_types=args.match_types
        )
        logging.info(f"Created {len(ad_groups)} ad groups")
    
    # Process competition data if provided
    competitor_keywords = []
    if args.spyfu and not args.dry_run:
        logging.info("Processing SpyFu competition data...")
        spyfu_data = input_parser.parse_spyfu_data(args.spyfu)
        # Process competition data (simplified for now)
        logging.info(f"Loaded {len(spyfu_data)} competitor keywords")
    
    # Scrape landing pages if provided
    scraped_data = []
    if args.urls and landing_page_scraper and not args.dry_run:
        logging.info("Scraping competitor landing pages...")
        competitor_urls = input_parser.parse_competitor_urls(args.urls)
        scraped_data = await landing_page_scraper.scrape_landing_pages(competitor_urls)
        
        if scraped_data:
            analysis = landing_page_scraper.analyze_copy_trends(scraped_data)
            logging.info(f"Scraped {analysis.get('successful_scrapes', 0)} pages successfully")
    
    # Export results
    logging.info("Exporting results...")
    
    if expanded_keywords:
        keywords_file = csv_exporter.export_keywords(expanded_keywords)
        logging.info(f"Exported keywords to {keywords_file}")
    
    if negative_keywords:
        negatives_file = csv_exporter.export_negative_keywords(negative_keywords)
        logging.info(f"Exported negative keywords to {negatives_file}")
    
    if ad_groups:
        ad_groups_file = csv_exporter.export_ad_groups(ad_groups)
        logging.info(f"Exported ad groups to {ad_groups_file}")
        
        # Export Google Ads format if requested
        if args.export_google:
            google_file = csv_exporter.export_google_ads_import(
                ad_groups, 
                negative_keywords,
                campaign_name=args.project
            )
            logging.info(f"Exported Google Ads import file to {google_file}")
    
    if scraped_data:
        copy_file = csv_exporter.export_scraped_copy(scraped_data)
        logging.info(f"Exported scraped copy to {copy_file}")
    
    # Export summary
    if expanded_keywords or ad_groups:
        summary_file = csv_exporter.export_campaign_summary(
            expanded_keywords,
            ad_groups,
            negative_keywords
        )
        logging.info(f"Exported campaign summary to {summary_file}")
    
    logging.info("Processing complete!")


def main():
    """Main entry point for PPC Keyword Automator."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logging.info("=== PPC Keyword Automator Started ===")
    logging.info(f"Project: {args.project}")
    
    try:
        # Initialize project manager
        project_manager = ProjectManager()
        
        # Get or create project
        project_path = project_manager.get_project_path(args.project)
        
        if not project_path:
            if args.create:
                logging.info(f"Creating new project: {args.project}")
                project_path = project_manager.create_project(args.project)
            else:
                logging.error(f"Project '{args.project}' not found. Use --create to create a new project.")
                return 1
        
        logging.info(f"Using project at: {project_path}")
        
        # Validate project structure
        is_valid, issues = project_manager.validate_project(args.project)
        if not is_valid:
            logging.warning(f"Project validation issues: {issues}")
        
        # Check for required inputs
        if not args.seeds and not args.dry_run:
            # Check project inputs directory
            project_seeds = project_path / "inputs" / "keywords" / "seed_keywords.txt"
            if project_seeds.exists():
                args.seeds = str(project_seeds)
                logging.info(f"Using project seed keywords: {project_seeds}")
            else:
                logging.error("No seed keywords provided. Use --seeds or add to project inputs.")
                return 1
        
        if not args.locations and not args.dry_run:
            # Check project inputs directory
            project_locations = project_path / "inputs" / "locations" / "cities.csv"
            if project_locations.exists():
                args.locations = str(project_locations)
                logging.info(f"Using project locations: {project_locations}")
        
        # Set output to project outputs directory if not specified
        if args.output == 'data/output':
            args.output = str(project_path / "outputs")
        
        # Run async processing
        import asyncio
        asyncio.run(process_keywords(args, project_path))
        
        logging.info("=== PPC Keyword Automator Completed ===")
        return 0
        
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Error in main process: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())