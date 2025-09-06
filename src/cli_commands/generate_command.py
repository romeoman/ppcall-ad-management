"""Implementation of the 'generate' CLI command."""

import logging
from pathlib import Path
import pandas as pd

from src.project_manager.project_manager import ProjectManager
from src.processors.ad_group_processor import AdGroupProcessor
from src.output_generator.csv_exporter import CSVExporter
from models.keyword_models import Keyword

logger = logging.getLogger(__name__)


def execute_generate(args, project_manager: ProjectManager) -> int:
    """
    Execute the generate command to create ad groups.
    
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
        
        logger.info(f"Generating ad groups for project '{args.project}'")
        
        # Initialize components
        ad_group_processor = AdGroupProcessor()
        csv_exporter = CSVExporter(str(project_path / "outputs" / "ad_groups"))
        
        # Find the most recent keywords file
        keywords_dir = project_path / "outputs" / "keywords"
        if not keywords_dir.exists():
            logger.error("No keywords found. Run 'ppc research' first.")
            return 1
        
        keyword_files = sorted(keywords_dir.glob("*keywords*.csv"))
        if not keyword_files:
            logger.error("No keyword CSV files found. Run 'ppc research' first.")
            return 1
        
        # Load keywords from most recent file
        latest_file = keyword_files[-1]
        logger.info(f"Loading keywords from {latest_file}")
        
        df = pd.read_csv(latest_file)
        keywords = []
        for _, row in df.iterrows():
            keywords.append(Keyword(
                term=row.get('Keyword', ''),
                category=row.get('Category'),
                location=row.get('Location'),
                volume=row.get('Volume', 0),
                cpc=row.get('CPC', 0.0),
                competition=row.get('Competition', 0.0)
            ))
        
        logger.info(f"Loaded {len(keywords)} keywords")
        
        # Generate ad groups
        logger.info(f"Creating ad groups with match types: {args.match_types}")
        ad_groups = ad_group_processor.create_ad_groups(
            keywords,
            match_types=args.match_types
        )
        
        # Apply grouping strategy
        if args.group_by != 'both':
            # Filter ad groups based on grouping
            if args.group_by == 'service':
                ad_groups = [ag for ag in ad_groups if 'General' not in ag.name]
            elif args.group_by == 'location':
                ad_groups = [ag for ag in ad_groups if not any(
                    svc in ag.name for svc in ['Emergency', 'Repair', 'Installation', 'Service']
                )]
        
        # Limit keywords per group if specified
        if args.max_keywords_per_group:
            for ad_group in ad_groups:
                if len(ad_group.keywords) > args.max_keywords_per_group:
                    ad_group.keywords = ad_group.keywords[:args.max_keywords_per_group]
        
        logger.info(f"Created {len(ad_groups)} ad groups")
        
        # Export ad groups
        output_file = csv_exporter.export_ad_groups(ad_groups)
        logger.info(f"✓ Ad groups exported to {output_file}")
        
        # Generate negative keywords if requested
        if args.include_negatives:
            from models.keyword_models import NegativeKeyword
            
            # Default negative keywords
            negative_keywords = [
                NegativeKeyword(term="free", reason="No monetization"),
                NegativeKeyword(term="diy", reason="Do-it-yourself"),
                NegativeKeyword(term="tutorial", reason="Educational content"),
                NegativeKeyword(term="jobs", reason="Job seekers"),
                NegativeKeyword(term="salary", reason="Employment related")
            ]
            
            neg_output = csv_exporter.export_negative_keywords(negative_keywords)
            logger.info(f"✓ Negative keywords exported to {neg_output}")
        
        print(f"\nAd group generation complete!")
        print(f"  - Total ad groups: {len(ad_groups)}")
        print(f"  - Match types: {', '.join(args.match_types)}")
        print(f"  - Output file: {output_file}")
        
        if args.include_negatives:
            print(f"  - Negative keywords generated")
        
        print(f"\nNext step: ppc export --project {args.project}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate ad groups: {e}", exc_info=True)
        return 1