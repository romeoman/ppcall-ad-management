"""Output and export data models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from pathlib import Path
from enum import Enum
import json


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    TSV = "tsv"
    GOOGLE_ADS = "google_ads"


class CSVExport(BaseModel):
    """CSV export configuration and data."""
    filename: str = Field(..., pattern="^[a-zA-Z0-9_-]+\\.(csv|tsv)$")
    headers: List[str]
    rows: List[Dict[str, Any]]
    delimiter: str = Field(default=",", pattern="^[,\\t|;]$")
    include_headers: bool = Field(default=True)
    quote_fields: bool = Field(default=True)
    encoding: str = Field(default="utf-8")
    
    @field_validator('filename')
    def validate_filename(cls, v):
        """Ensure filename has correct extension."""
        if not v.endswith(('.csv', '.tsv')):
            v += '.csv'
        return v
    
    def get_row_count(self) -> int:
        """Get number of data rows."""
        return len(self.rows)
    
    def to_csv_string(self) -> str:
        """Convert to CSV string format."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.headers,
            delimiter=self.delimiter,
            quoting=csv.QUOTE_ALL if self.quote_fields else csv.QUOTE_MINIMAL
        )
        
        if self.include_headers:
            writer.writeheader()
        writer.writerows(self.rows)
        
        return output.getvalue()


class GoogleAdsExport(BaseModel):
    """Google Ads specific export format."""
    campaign_name: str = Field(..., min_length=1, max_length=255)
    export_type: str = Field(..., pattern="^(keywords|ads|ad_groups|campaigns|negative_keywords)$")
    
    # Google Ads specific fields
    keywords_data: Optional[List[Dict[str, Any]]] = None
    ad_groups_data: Optional[List[Dict[str, Any]]] = None
    negative_keywords_data: Optional[List[Dict[str, Any]]] = None
    campaigns_data: Optional[List[Dict[str, Any]]] = None
    
    include_match_types: bool = Field(default=True)
    include_bids: bool = Field(default=True)
    include_urls: bool = Field(default=False)
    use_editor_format: bool = Field(default=True, description="Use Google Ads Editor format")
    
    def to_editor_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to Google Ads Editor format."""
        editor_data = {}
        
        if self.keywords_data:
            editor_data["Keywords"] = [
                {
                    "Campaign": self.campaign_name,
                    "Ad Group": kw.get("ad_group", ""),
                    "Keyword": kw.get("keyword", ""),
                    "Match Type": kw.get("match_type", "Broad"),
                    "Max CPC": kw.get("bid", ""),
                    "Final URL": kw.get("final_url", "") if self.include_urls else "",
                }
                for kw in self.keywords_data
            ]
        
        if self.negative_keywords_data:
            editor_data["Campaign Negative Keywords"] = [
                {
                    "Campaign": self.campaign_name,
                    "Negative Keyword": nk.get("keyword", ""),
                    "Match Type": nk.get("match_type", "Phrase"),
                }
                for nk in self.negative_keywords_data
            ]
        
        return editor_data
    
    def validate_for_import(self) -> List[str]:
        """Validate data meets Google Ads import requirements."""
        errors = []
        
        if self.keywords_data:
            for i, kw in enumerate(self.keywords_data):
                # Check keyword length
                if len(kw.get("keyword", "")) > 80:
                    errors.append(f"Keyword {i}: exceeds 80 character limit")
                
                # Check bid values
                bid = kw.get("bid")
                if bid and (bid < 0.01 or bid > 5000):
                    errors.append(f"Keyword {i}: bid must be between $0.01 and $5000")
                
                # Check match type
                valid_match_types = ["Broad", "Phrase", "Exact", "Broad match modifier"]
                if kw.get("match_type") not in valid_match_types:
                    errors.append(f"Keyword {i}: invalid match type")
        
        return errors


class ProjectExport(BaseModel):
    """Complete project export package."""
    project_name: str
    export_date: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    
    # Export components
    keywords_export: Optional[CSVExport] = None
    negative_keywords_export: Optional[CSVExport] = None
    ad_groups_export: Optional[CSVExport] = None
    competitor_analysis_export: Optional[CSVExport] = None
    landing_pages_export: Optional[CSVExport] = None
    
    # Google Ads specific exports
    google_ads_exports: List[GoogleAdsExport] = Field(default_factory=list)
    
    # Archive settings
    create_zip: bool = Field(default=True)
    include_config: bool = Field(default=True)
    include_metadata: bool = Field(default=True)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_file_list(self) -> List[str]:
        """Get list of files to be exported."""
        files = []
        
        if self.keywords_export:
            files.append(self.keywords_export.filename)
        if self.negative_keywords_export:
            files.append(self.negative_keywords_export.filename)
        if self.ad_groups_export:
            files.append(self.ad_groups_export.filename)
        if self.competitor_analysis_export:
            files.append(self.competitor_analysis_export.filename)
        if self.landing_pages_export:
            files.append(self.landing_pages_export.filename)
        
        for gads_export in self.google_ads_exports:
            files.append(f"{gads_export.campaign_name}_{gads_export.export_type}.csv")
        
        if self.include_metadata:
            files.append("metadata.json")
        if self.include_config:
            files.append("config.json")
        
        return files
    
    def create_metadata_json(self) -> str:
        """Create metadata JSON for the export."""
        metadata = {
            "project_name": self.project_name,
            "export_date": self.export_date.isoformat(),
            "version": self.version,
            "files": self.get_file_list(),
            "statistics": {
                "total_keywords": len(self.keywords_export.rows) if self.keywords_export else 0,
                "total_negative_keywords": len(self.negative_keywords_export.rows) if self.negative_keywords_export else 0,
                "total_ad_groups": len(self.ad_groups_export.rows) if self.ad_groups_export else 0,
            },
            "custom_metadata": self.metadata
        }
        
        return json.dumps(metadata, indent=2)


class ConsolidatedOutput(BaseModel):
    """Consolidated output for all campaign data."""
    campaign_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Summary statistics
    total_keywords: int = Field(default=0, ge=0)
    total_ad_groups: int = Field(default=0, ge=0)
    total_negative_keywords: int = Field(default=0, ge=0)
    estimated_monthly_searches: int = Field(default=0, ge=0)
    average_cpc: float = Field(default=0.0, ge=0)
    
    # Data sections
    keywords_by_category: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    keywords_by_location: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    ad_groups_summary: List[Dict[str, Any]] = Field(default_factory=list)
    competitor_insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Performance estimates
    estimated_clicks: Optional[int] = None
    estimated_impressions: Optional[int] = None
    estimated_cost: Optional[float] = None
    estimated_conversions: Optional[int] = None
    
    @field_validator('average_cpc', 'estimated_cost')
    def round_money(cls, v):
        """Round monetary values to 2 decimal places."""
        return round(v, 2) if v else 0.0
    
    def generate_summary_report(self) -> str:
        """Generate a text summary report."""
        report = f"""
Campaign Summary Report
=======================
Campaign: {self.campaign_name}
Generated: {self.created_at.strftime('%Y-%m-%d %H:%M')}

Key Metrics:
- Total Keywords: {self.total_keywords:,}
- Total Ad Groups: {self.total_ad_groups:,}
- Negative Keywords: {self.total_negative_keywords:,}
- Est. Monthly Searches: {self.estimated_monthly_searches:,}
- Average CPC: ${self.average_cpc:.2f}

Categories: {len(self.keywords_by_category)}
Locations: {len(self.keywords_by_location)}

Performance Estimates:
- Estimated Clicks: {self.estimated_clicks:,} per month
- Estimated Impressions: {self.estimated_impressions:,} per month
- Estimated Cost: ${self.estimated_cost:,.2f} per month
"""
        return report.strip()


class ExportConfig(BaseModel):
    """Configuration for export operations."""
    output_directory: Path
    formats: List[ExportFormat] = Field(default_factory=lambda: [ExportFormat.CSV, ExportFormat.GOOGLE_ADS])
    compress: bool = Field(default=True)
    split_by_ad_group: bool = Field(default=False)
    max_keywords_per_file: Optional[int] = Field(None, ge=100, le=10000)
    include_timestamps: bool = Field(default=True)
    naming_convention: str = Field(default="{project}_{type}_{date}")
    
    @field_validator('output_directory')
    def validate_directory(cls, v):
        """Ensure output directory exists or can be created."""
        v = Path(v)
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v