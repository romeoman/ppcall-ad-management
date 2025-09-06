"""Implementation of the 'export' CLI command."""

import logging
from pathlib import Path
import pandas as pd
import shutil
from datetime import datetime

from src.project_manager.project_manager import ProjectManager
from src.output_generator.csv_exporter import CSVExporter
from src.output_generator.export_manager import ExportManager
from models.keyword_models import Keyword, NegativeKeyword
from models.ad_group_models import AdGroup

logger = logging.getLogger(__name__)


def execute_export(args, project_manager: ProjectManager) -> int:
    """
    Execute the export command to generate campaign files using ExportManager.
    
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
        
        logger.info(f"Exporting campaign data for project '{args.project}'")
        
        # Determine output directory
        output_dir = Path(args.output) if args.output else None
        
        # Initialize ExportManager
        export_manager = ExportManager(project_path, output_dir)
        
        # Determine formats to export
        if args.format == 'all':
            formats = ['google', 'bing', 'csv']
        else:
            formats = [args.format]
        
        # Perform export using ExportManager
        result = export_manager.export_from_project(
            formats=formats,
            create_zip=args.zip,
            include_settings=args.include_settings,
            validate_google_ads=True  # Always validate for Google Ads
        )
        
        if result['success']:
            # Display results
            print(f"\nExport complete!")
            print(f"  - Campaign: {args.project}")
            print(f"  - Format(s): {', '.join(formats)}")
            print(f"  - Files exported: {len(result['exported_files'])}")
            print(f"  - Output directory: {result['output_directory']}")
            
            # Display statistics
            stats = result['statistics']
            print("\nData Summary:")
            print(f"  - Keywords: {stats['keywords_count']}")
            print(f"  - Ad Groups: {stats['ad_groups_count']}")
            print(f"  - Negative Keywords: {stats['negative_keywords_count']}")
            
            if stats['competitor_keywords_count'] > 0:
                print(f"  - Competitor Keywords: {stats['competitor_keywords_count']}")
            
            if stats['scraped_pages_count'] > 0:
                print(f"  - Scraped Pages: {stats['scraped_pages_count']}")
            
            # Display validation results if any warnings
            if stats.get('validation_results') and stats['validation_results'].get('warnings'):
                warnings = stats['validation_results']['warnings']
                print(f"\n⚠️  Google Ads Validation Warnings ({len(warnings)}):")
                for warning in warnings[:5]:  # Show first 5 warnings
                    print(f"  - {warning}")
                if len(warnings) > 5:
                    print(f"  ... and {len(warnings) - 5} more warnings")
            
            if result.get('zip_path'):
                print(f"\n✓ ZIP archive created: {Path(result['zip_path']).name}")
            
            print("\nExported files:")
            for file_path in result['exported_files'][:10]:  # Show first 10 files
                print(f"  - {Path(file_path).name}")
            if len(result['exported_files']) > 10:
                print(f"  ... and {len(result['exported_files']) - 10} more files")
            
            return 0
        else:
            logger.error("Export failed")
            return 1
        
    except Exception as e:
        logger.error(f"Failed to export campaign: {e}", exc_info=True)
        return 1


def load_keywords(project_path: Path):
    """Load keywords from project outputs."""
    keywords = []
    keywords_dir = project_path / "outputs" / "keywords"
    
    if keywords_dir.exists():
        keyword_files = sorted(keywords_dir.glob("*keywords*.csv"))
        if keyword_files:
            df = pd.read_csv(keyword_files[-1])
            for _, row in df.iterrows():
                keywords.append(Keyword(
                    term=row.get('Keyword', ''),
                    category=row.get('Category'),
                    location=row.get('Location'),
                    volume=row.get('Volume', 0),
                    cpc=row.get('CPC', 0.0),
                    competition=row.get('Competition', 0.0)
                ))
    
    return keywords


def load_ad_groups(project_path: Path):
    """Load ad groups from project outputs."""
    ad_groups = []
    ad_groups_dir = project_path / "outputs" / "ad_groups"
    
    if ad_groups_dir.exists():
        ag_files = sorted(ad_groups_dir.glob("*ad_groups*.csv"))
        if ag_files:
            df = pd.read_csv(ag_files[-1])
            
            # Group by ad group name
            grouped = df.groupby('Ad Group')
            for name, group in grouped:
                keywords = group['Keyword'].tolist()
                match_type = group['Match Type'].iloc[0].lower() if not group.empty else 'broad'
                
                ad_groups.append(AdGroup(
                    name=name,
                    keywords=keywords,
                    match_type=match_type
                ))
    
    return ad_groups


def load_negative_keywords(project_path: Path):
    """Load negative keywords from project."""
    negative_keywords = []
    
    # Check outputs directory first
    neg_dir = project_path / "outputs" / "negatives"
    if neg_dir.exists():
        neg_files = sorted(neg_dir.glob("*negative*.csv"))
        if neg_files:
            df = pd.read_csv(neg_files[-1])
            for _, row in df.iterrows():
                negative_keywords.append(NegativeKeyword(
                    term=row.get('Negative Keyword', ''),
                    reason=row.get('Reason', '')
                ))
            return negative_keywords
    
    # Fall back to input directory
    neg_file = project_path / "inputs" / "keywords" / "negative_keywords.txt"
    if neg_file.exists():
        with open(neg_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    negative_keywords.append(NegativeKeyword(term=line))
    
    return negative_keywords