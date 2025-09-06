"""Consolidated export and consolidation module for PPC campaign data."""

import logging
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import zipfile
import pandas as pd

from models.keyword_models import Keyword, NegativeKeyword
from models.ad_group_models import AdGroup
from models.competition_models import CompetitorKeyword, ScrapedCopy
from src.output_generator.csv_exporter import CSVExporter

logger = logging.getLogger(__name__)


class ExportManager:
    """Manages consolidated exports, ZIP archives, and Google Ads formatting."""
    
    def __init__(self, project_path: Path, output_dir: Optional[Path] = None):
        """
        Initialize ExportManager.
        
        Args:
            project_path: Path to project root directory
            output_dir: Custom output directory (defaults to project_path/outputs/exports)
        """
        self.project_path = Path(project_path)
        self.output_dir = output_dir or self.project_path / "outputs" / "exports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV exporter
        self.csv_exporter = CSVExporter(str(self.output_dir))
        
        # Track exported files and statistics
        self.exported_files = []
        self.export_stats = {}
        
        logger.info(f"ExportManager initialized for project: {self.project_path}")
    
    def export_full_campaign(
        self,
        keywords: List[Keyword],
        ad_groups: List[AdGroup],
        negative_keywords: List[NegativeKeyword],
        competitor_keywords: Optional[List[CompetitorKeyword]] = None,
        scraped_copy: Optional[List[ScrapedCopy]] = None,
        campaign_name: str = "PPC Campaign",
        formats: List[str] = ["google", "csv"],
        create_zip: bool = True,
        include_settings: bool = True,
        validate_google_ads: bool = True
    ) -> Dict[str, Any]:
        """
        Export complete campaign with all data types.
        
        Args:
            keywords: List of keywords
            ad_groups: List of ad groups
            negative_keywords: List of negative keywords
            competitor_keywords: Optional competitor analysis data
            scraped_copy: Optional scraped landing page data
            campaign_name: Campaign name for exports
            formats: Export formats ("google", "bing", "csv", "all")
            create_zip: Whether to create ZIP archive
            include_settings: Include project configuration in export
            validate_google_ads: Validate Google Ads compatibility
            
        Returns:
            Dictionary with export results and statistics
        """
        logger.info(f"Starting full campaign export for '{campaign_name}'")
        
        # Reset tracking
        self.exported_files = []
        self.export_stats = {
            "campaign_name": campaign_name,
            "export_timestamp": datetime.now().isoformat(),
            "keywords_count": len(keywords),
            "ad_groups_count": len(ad_groups),
            "negative_keywords_count": len(negative_keywords),
            "competitor_keywords_count": len(competitor_keywords) if competitor_keywords else 0,
            "scraped_pages_count": len(scraped_copy) if scraped_copy else 0,
            "formats_exported": formats,
            "validation_results": {}
        }
        
        # Validate Google Ads format if requested
        if validate_google_ads and ("google" in formats or "all" in formats):
            validation_results = self._validate_google_ads_format(
                ad_groups, negative_keywords
            )
            self.export_stats["validation_results"] = validation_results
            
            if not validation_results["is_valid"]:
                logger.warning(f"Google Ads validation warnings: {validation_results['warnings']}")
        
        # Export based on requested formats
        if "all" in formats:
            formats = ["google", "bing", "csv"]
        
        for format_type in formats:
            self._export_format(
                format_type,
                keywords,
                ad_groups,
                negative_keywords,
                competitor_keywords,
                scraped_copy,
                campaign_name
            )
        
        # Export campaign summary
        summary_file = self._export_campaign_summary(
            keywords, ad_groups, negative_keywords
        )
        self.exported_files.append(summary_file)
        
        # Include project settings if requested
        if include_settings:
            self._include_project_settings()
        
        # Create consolidated ZIP archive if requested
        zip_path = None
        if create_zip and self.exported_files:
            zip_path = self._create_consolidated_zip(campaign_name)
            self.export_stats["zip_archive"] = str(zip_path)
        
        # Generate and save export summary
        summary = self._generate_export_summary()
        self._save_export_summary(summary)
        
        # Log summary statistics
        self._log_export_summary()
        
        return {
            "success": True,
            "exported_files": self.exported_files,
            "zip_path": zip_path,
            "statistics": self.export_stats,
            "output_directory": str(self.output_dir)
        }
    
    def _export_format(
        self,
        format_type: str,
        keywords: List[Keyword],
        ad_groups: List[AdGroup],
        negative_keywords: List[NegativeKeyword],
        competitor_keywords: Optional[List[CompetitorKeyword]],
        scraped_copy: Optional[List[ScrapedCopy]],
        campaign_name: str
    ):
        """Export data in specified format."""
        logger.info(f"Exporting {format_type} format")
        
        if format_type == "google":
            file_path = self.csv_exporter.export_google_ads_import(
                ad_groups, negative_keywords, campaign_name
            )
            self.exported_files.append(file_path)
            logger.info(f"✓ Google Ads export: {file_path.name}")
            
        elif format_type == "bing":
            # Use Google format with Bing naming for now
            file_path = self.csv_exporter.export_google_ads_import(
                ad_groups, negative_keywords, f"{campaign_name}_bing",
                filename="bing_ads_import.csv"
            )
            self.exported_files.append(file_path)
            logger.info(f"✓ Bing Ads export: {file_path.name}")
            
        elif format_type == "csv":
            # Export individual CSV files
            if keywords:
                kw_file = self.csv_exporter.export_keywords(keywords)
                self.exported_files.append(kw_file)
                logger.info(f"✓ Keywords CSV: {kw_file.name}")
            
            if ad_groups:
                ag_file = self.csv_exporter.export_ad_groups(ad_groups)
                self.exported_files.append(ag_file)
                logger.info(f"✓ Ad groups CSV: {ag_file.name}")
            
            if negative_keywords:
                neg_file = self.csv_exporter.export_negative_keywords(negative_keywords)
                self.exported_files.append(neg_file)
                logger.info(f"✓ Negative keywords CSV: {neg_file.name}")
            
            if competitor_keywords:
                comp_file = self.csv_exporter.export_competition_report(competitor_keywords)
                self.exported_files.append(comp_file)
                logger.info(f"✓ Competition report CSV: {comp_file.name}")
            
            if scraped_copy:
                scrape_file = self.csv_exporter.export_scraped_copy(scraped_copy)
                self.exported_files.append(scrape_file)
                logger.info(f"✓ Scraped copy CSV: {scrape_file.name}")
    
    def _validate_google_ads_format(
        self,
        ad_groups: List[AdGroup],
        negative_keywords: List[NegativeKeyword]
    ) -> Dict[str, Any]:
        """
        Validate data for Google Ads compatibility.
        
        Returns:
            Dictionary with validation results
        """
        warnings = []
        errors = []
        
        # Validate ad groups
        for ad_group in ad_groups:
            # Check ad group name length (max 255 characters)
            if len(ad_group.name) > 255:
                errors.append(f"Ad group name too long: {ad_group.name[:50]}...")
            
            # Get keywords list - handle both full model and simplified version
            keywords_list = self._get_keywords_list(ad_group)
            
            # Check for empty keywords
            if not keywords_list:
                warnings.append(f"Ad group has no keywords: {ad_group.name}")
            
            # Validate keywords
            for keyword in keywords_list:
                # Extract keyword string if it's an object
                keyword_str = self._get_keyword_string(keyword)
                
                # Check keyword length (max 80 characters excluding match type syntax)
                clean_keyword = keyword_str.strip('[]"')
                if len(clean_keyword) > 80:
                    warnings.append(f"Keyword too long: {clean_keyword[:50]}...")
                
                # Check for invalid characters
                if any(char in clean_keyword for char in ['!', '@', '#', '$', '%', '^', '&', '*']):
                    warnings.append(f"Keyword contains invalid characters: {clean_keyword}")
            
            # Validate max CPC - check both max_cpc and default_bid
            max_cpc = getattr(ad_group, 'max_cpc', None) or getattr(ad_group, 'default_bid', None)
            if max_cpc and max_cpc > 10000:
                warnings.append(f"Max CPC exceeds Google Ads limit: ${max_cpc}")
        
        # Validate negative keywords
        for neg_keyword in negative_keywords:
            if len(neg_keyword.term) > 80:
                warnings.append(f"Negative keyword too long: {neg_keyword.term[:50]}...")
        
        # Check total counts
        total_keywords = sum(len(self._get_keywords_list(ag)) for ag in ad_groups)
        if total_keywords > 20000:
            warnings.append(f"Total keywords ({total_keywords}) exceeds recommended limit of 20,000")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_keywords": total_keywords,
            "total_ad_groups": len(ad_groups),
            "total_negatives": len(negative_keywords)
        }
    
    def _get_keywords_list(self, ad_group) -> List:
        """Extract keywords list from ad group, handling different structures."""
        if hasattr(ad_group, 'keywords'):
            return ad_group.keywords
        return []
    
    def _get_keyword_string(self, keyword) -> str:
        """Extract keyword string from keyword object or string."""
        if isinstance(keyword, str):
            return keyword
        elif hasattr(keyword, 'keyword') and hasattr(keyword.keyword, 'term'):
            return keyword.keyword.term
        elif hasattr(keyword, 'term'):
            return keyword.term
        return str(keyword)
    
    def _export_campaign_summary(
        self,
        keywords: List[Keyword],
        ad_groups: List[AdGroup],
        negative_keywords: List[NegativeKeyword]
    ) -> Path:
        """Export detailed campaign summary."""
        return self.csv_exporter.export_campaign_summary(
            keywords, ad_groups, negative_keywords
        )
    
    def _include_project_settings(self):
        """Include project configuration files in export."""
        config_dir = self.project_path / "configs"
        
        if config_dir.exists():
            # Copy all config files
            config_files = ["project_config.json", "campaign_settings.json", 
                          "processing_rules.json", "api_config.json"]
            
            for config_file in config_files:
                source = config_dir / config_file
                if source.exists():
                    dest = self.output_dir / config_file
                    shutil.copy2(source, dest)
                    self.exported_files.append(dest)
                    logger.info(f"✓ Included config: {config_file}")
        
        # Include project metadata
        metadata_file = self.project_path / "metadata.json"
        if metadata_file.exists():
            dest = self.output_dir / "project_metadata.json"
            shutil.copy2(metadata_file, dest)
            self.exported_files.append(dest)
            logger.info("✓ Included project metadata")
    
    def _create_consolidated_zip(self, campaign_name: str) -> Path:
        """
        Create consolidated ZIP archive of all exports.
        
        Args:
            campaign_name: Name for the ZIP file
            
        Returns:
            Path to created ZIP file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"{campaign_name}_complete_export_{timestamp}.zip"
        zip_path = self.output_dir / zip_name
        
        logger.info(f"Creating consolidated ZIP archive: {zip_name}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all exported files
            for file_path in self.exported_files:
                if file_path.exists():
                    arcname = file_path.name
                    zipf.write(file_path, arcname)
                    logger.debug(f"Added to ZIP: {arcname}")
            
            # Add export summary
            summary_data = self._generate_export_summary()
            zipf.writestr("export_summary.json", json.dumps(summary_data, indent=2))
        
        # Calculate ZIP size
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        self.export_stats["zip_size_mb"] = round(zip_size_mb, 2)
        
        logger.info(f"✓ ZIP archive created: {zip_name} ({zip_size_mb:.2f} MB)")
        
        return zip_path
    
    def _generate_export_summary(self) -> Dict[str, Any]:
        """Generate comprehensive export summary."""
        return {
            "export_info": {
                "timestamp": self.export_stats["export_timestamp"],
                "campaign_name": self.export_stats["campaign_name"],
                "output_directory": str(self.output_dir),
                "project_path": str(self.project_path)
            },
            "data_statistics": {
                "keywords": {
                    "total": self.export_stats["keywords_count"],
                    "message": f"{self.export_stats['keywords_count']} keywords generated"
                },
                "ad_groups": {
                    "total": self.export_stats["ad_groups_count"],
                    "message": f"{self.export_stats['ad_groups_count']} ad groups created"
                },
                "negative_keywords": {
                    "total": self.export_stats["negative_keywords_count"],
                    "message": f"{self.export_stats['negative_keywords_count']} negative keywords identified"
                },
                "competitor_keywords": {
                    "total": self.export_stats["competitor_keywords_count"],
                    "message": f"{self.export_stats['competitor_keywords_count']} competitor keywords analyzed"
                },
                "scraped_pages": {
                    "total": self.export_stats["scraped_pages_count"],
                    "message": f"{self.export_stats['scraped_pages_count']} landing pages scraped"
                }
            },
            "exported_files": {
                "count": len(self.exported_files),
                "files": [str(f.name) for f in self.exported_files]
            },
            "validation": self.export_stats.get("validation_results", {}),
            "formats": self.export_stats["formats_exported"]
        }
    
    def _save_export_summary(self, summary: Dict[str, Any]):
        """Save export summary to JSON file."""
        summary_path = self.output_dir / "export_summary.json"
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.exported_files.append(summary_path)
        logger.info(f"✓ Export summary saved: {summary_path.name}")
    
    def _log_export_summary(self):
        """Log comprehensive export summary."""
        logger.info("=" * 60)
        logger.info("EXPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Campaign: {self.export_stats['campaign_name']}")
        logger.info(f"Timestamp: {self.export_stats['export_timestamp']}")
        logger.info("-" * 40)
        logger.info("Data Generated:")
        logger.info(f"  • {self.export_stats['keywords_count']} keywords generated")
        logger.info(f"  • {self.export_stats['ad_groups_count']} ad groups created")
        logger.info(f"  • {self.export_stats['negative_keywords_count']} negative keywords identified")
        
        if self.export_stats['competitor_keywords_count'] > 0:
            logger.info(f"  • {self.export_stats['competitor_keywords_count']} competitor keywords analyzed")
        
        if self.export_stats['scraped_pages_count'] > 0:
            logger.info(f"  • {self.export_stats['scraped_pages_count']} landing pages scraped")
        
        logger.info("-" * 40)
        logger.info(f"Files Exported: {len(self.exported_files)}")
        logger.info(f"Formats: {', '.join(self.export_stats['formats_exported'])}")
        
        if "zip_archive" in self.export_stats:
            logger.info(f"ZIP Archive: {Path(self.export_stats['zip_archive']).name}")
            logger.info(f"ZIP Size: {self.export_stats.get('zip_size_mb', 0)} MB")
        
        if self.export_stats.get("validation_results"):
            validation = self.export_stats["validation_results"]
            if validation.get("warnings"):
                logger.warning(f"Validation Warnings: {len(validation['warnings'])}")
        
        logger.info(f"Output Directory: {self.output_dir}")
        logger.info("=" * 60)
    
    def export_from_project(
        self,
        formats: List[str] = ["google", "csv"],
        create_zip: bool = True,
        include_settings: bool = True,
        validate_google_ads: bool = True
    ) -> Dict[str, Any]:
        """
        Export campaign data directly from project structure.
        
        This method loads data from the project's output directories
        and exports it in the requested formats.
        
        Args:
            formats: Export formats to generate
            create_zip: Whether to create ZIP archive
            include_settings: Include project configuration
            validate_google_ads: Validate Google Ads compatibility
            
        Returns:
            Dictionary with export results
        """
        logger.info(f"Loading data from project: {self.project_path}")
        
        # Load data from project outputs
        keywords = self._load_keywords_from_project()
        ad_groups = self._load_ad_groups_from_project()
        negative_keywords = self._load_negative_keywords_from_project()
        competitor_keywords = self._load_competitor_keywords_from_project()
        scraped_copy = self._load_scraped_copy_from_project()
        
        # Get campaign name from project
        campaign_name = self.project_path.name
        
        # Export full campaign
        return self.export_full_campaign(
            keywords=keywords,
            ad_groups=ad_groups,
            negative_keywords=negative_keywords,
            competitor_keywords=competitor_keywords,
            scraped_copy=scraped_copy,
            campaign_name=campaign_name,
            formats=formats,
            create_zip=create_zip,
            include_settings=include_settings,
            validate_google_ads=validate_google_ads
        )
    
    def _load_keywords_from_project(self) -> List[Keyword]:
        """Load keywords from project outputs."""
        keywords = []
        keywords_dir = self.project_path / "outputs" / "keywords"
        
        if keywords_dir.exists():
            # Find most recent keywords file
            keyword_files = sorted(keywords_dir.glob("*keywords*.csv"))
            if keyword_files:
                latest_file = keyword_files[-1]
                logger.info(f"Loading keywords from: {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                for _, row in df.iterrows():
                    keywords.append(Keyword(
                        term=row.get('Keyword', ''),
                        category=row.get('Category'),
                        location=row.get('Location'),
                        volume=row.get('Volume', 0),
                        cpc=row.get('CPC', 0.0),
                        competition=row.get('Competition', 0.0),
                        intent=row.get('Intent'),
                        difficulty=row.get('Difficulty', 0)
                    ))
        
        return keywords
    
    def _load_ad_groups_from_project(self) -> List[AdGroup]:
        """Load ad groups from project outputs."""
        ad_groups = []
        ad_groups_dir = self.project_path / "outputs" / "ad_groups"
        
        if ad_groups_dir.exists():
            ag_files = sorted(ad_groups_dir.glob("*ad_groups*.csv"))
            if ag_files:
                latest_file = ag_files[-1]
                logger.info(f"Loading ad groups from: {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                
                # Group by ad group name
                grouped = df.groupby('Ad Group')
                for name, group in grouped:
                    keywords = group['Keyword'].tolist()
                    match_type = group['Match Type'].iloc[0].lower() if not group.empty else 'broad'
                    campaign = group['Campaign'].iloc[0] if 'Campaign' in group.columns else None
                    max_cpc = group['Max CPC'].iloc[0] if 'Max CPC' in group.columns else None
                    
                    ad_groups.append(AdGroup(
                        name=name,
                        keywords=keywords,
                        match_type=match_type,
                        campaign_name=campaign,
                        max_cpc=max_cpc
                    ))
        
        return ad_groups
    
    def _load_negative_keywords_from_project(self) -> List[NegativeKeyword]:
        """Load negative keywords from project."""
        negative_keywords = []
        
        # Check outputs directory first
        neg_dir = self.project_path / "outputs" / "negatives"
        if neg_dir.exists():
            neg_files = sorted(neg_dir.glob("*negative*.csv"))
            if neg_files:
                latest_file = neg_files[-1]
                logger.info(f"Loading negative keywords from: {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                for _, row in df.iterrows():
                    negative_keywords.append(NegativeKeyword(
                        term=row.get('Negative Keyword', ''),
                        match_type=row.get('Match Type', 'broad'),
                        reason=row.get('Reason', ''),
                        category=row.get('Category', '')
                    ))
                return negative_keywords
        
        # Fall back to input directory
        neg_file = self.project_path / "inputs" / "keywords" / "negative_keywords.txt"
        if neg_file.exists():
            logger.info(f"Loading negative keywords from: {neg_file.name}")
            
            with open(neg_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        negative_keywords.append(NegativeKeyword(
                            term=line,
                            match_type='broad'
                        ))
        
        return negative_keywords
    
    def _load_competitor_keywords_from_project(self) -> Optional[List[CompetitorKeyword]]:
        """Load competitor keywords from project."""
        competitor_keywords = []
        analysis_dir = self.project_path / "outputs" / "analysis"
        
        if analysis_dir.exists():
            comp_files = sorted(analysis_dir.glob("*competition*.csv"))
            if comp_files:
                latest_file = comp_files[-1]
                logger.info(f"Loading competitor data from: {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                for _, row in df.iterrows():
                    competitor_keywords.append(CompetitorKeyword(
                        competitor=row.get('Competitor', ''),
                        term=row.get('Keyword', ''),
                        position=row.get('Position'),
                        volume=row.get('Volume', 0),
                        cpc=row.get('CPC', 0.0),
                        competition=row.get('Competition', 0.0),
                        overlap=row.get('Overlap', '').lower() == 'yes',
                        recommendation=row.get('Recommendation', '')
                    ))
        
        return competitor_keywords if competitor_keywords else None
    
    def _load_scraped_copy_from_project(self) -> Optional[List[ScrapedCopy]]:
        """Load scraped copy data from project."""
        scraped_copy = []
        analysis_dir = self.project_path / "outputs" / "analysis"
        
        if analysis_dir.exists():
            scrape_files = sorted(analysis_dir.glob("*scraped*.csv"))
            if scrape_files:
                latest_file = scrape_files[-1]
                logger.info(f"Loading scraped data from: {latest_file.name}")
                
                df = pd.read_csv(latest_file)
                for _, row in df.iterrows():
                    scraped_copy.append(ScrapedCopy(
                        url=row.get('URL', ''),
                        domain=row.get('Domain', ''),
                        headline=row.get('Headline', ''),
                        subheadline=row.get('Subheadline', ''),
                        body_snippet=row.get('Body Snippet', ''),
                        cta=row.get('CTA', ''),
                        secondary_ctas=row.get('Secondary CTAs', '').split(', ') if row.get('Secondary CTAs') else [],
                        features=row.get('Features', '').split(', ') if row.get('Features') else [],
                        pricing=row.get('Pricing', ''),
                        testimonials=row.get('Testimonials', '').split(' | ') if row.get('Testimonials') else [],
                        meta_title=row.get('Meta Title', ''),
                        meta_description=row.get('Meta Description', ''),
                        scrape_success=row.get('Scrape Success', '').lower() == 'yes'
                    ))
        
        return scraped_copy if scraped_copy else None