"""Implementation of the 'research' CLI command."""

import logging
import asyncio
from pathlib import Path
import os

from src.project_manager.project_manager import ProjectManager
from api_integration.dataforseo_client import DataForSEOClient
from src.processors.keyword_processor import KeywordProcessor
from src.input_parser.parsers import InputParser
from src.output_generator.csv_exporter import CSVExporter

logger = logging.getLogger(__name__)


async def execute_research(args, project_manager: ProjectManager) -> int:
    """
    Execute the research command to expand keywords.
    
    Args:
        args: Command line arguments
        project_manager: ProjectManager instance
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Get project path
        project_path = project_manager.get_project_path(args.project)
        if not project_path:
            logger.error(f"Project '{args.project}' not found")
            return 1
        
        logger.info(f"Starting keyword research for project '{args.project}'")
        
        # Initialize components
        input_parser = InputParser()
        csv_exporter = CSVExporter(str(project_path / "outputs" / "keywords"))
        
        # Initialize API client
        dataforseo_client = DataForSEOClient(
            os.getenv('DATAFORSEO_LOGIN'),
            os.getenv('DATAFORSEO_PASSWORD')
        )
        keyword_processor = KeywordProcessor(dataforseo_client)
        
        # Load seed keywords
        seeds_file = args.seeds or str(project_path / "inputs" / "keywords" / "seed_keywords.txt")
        if not Path(seeds_file).exists():
            logger.error(f"Seed keywords file not found: {seeds_file}")
            return 1
        
        seed_keywords = input_parser.parse_seed_keywords(seeds_file)
        logger.info(f"Loaded {len(seed_keywords)} seed keywords")
        
        # Load locations if provided
        locations = []
        locations_file = args.locations or str(project_path / "inputs" / "locations" / "cities.csv")
        if Path(locations_file).exists():
            locations = input_parser.parse_locations(locations_file)
            logger.info(f"Loaded {len(locations)} locations")
        
        # Expand keywords
        logger.info(f"Expanding keywords with depth={args.depth}")
        expanded_keywords = await keyword_processor.expand_seed_keywords(seed_keywords)
        
        # Combine with locations if available
        if locations:
            logger.info("Combining keywords with locations")
            expanded_keywords = keyword_processor.combine_with_locations(
                expanded_keywords,
                locations
            )
        
        # Apply filters
        logger.info(f"Applying filters (min_volume={args.min_volume}, max_cpc={args.max_cpc})")
        filtered_keywords = keyword_processor.filter_keywords(
            expanded_keywords,
            min_volume=args.min_volume,
            max_cpc=args.max_cpc
        )
        
        logger.info(f"Generated {len(filtered_keywords)} keywords after filtering")
        
        # Export results
        output_file = csv_exporter.export_keywords(filtered_keywords)
        logger.info(f"✓ Keywords exported to {output_file}")
        
        print(f"\nKeyword research complete!")
        print(f"  - Seed keywords: {len(seed_keywords)}")
        print(f"  - Expanded keywords: {len(expanded_keywords)}")
        print(f"  - Filtered keywords: {len(filtered_keywords)}")
        print(f"  - Output file: {output_file}")
        print(f"\nNext step: ppc generate --project {args.project}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to execute research: {e}", exc_info=True)
        return 1