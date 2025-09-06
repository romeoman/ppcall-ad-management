"""CSV export functionality for PPC campaign data."""

import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from models.keyword_models import Keyword, NegativeKeyword
from models.ad_group_models import AdGroup
from models.competition_models import CompetitorKeyword, ScrapedCopy, KeywordGap

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export PPC campaign data to CSV files."""
    
    def __init__(self, output_dir: str = 'data/output'):
        """
        Initialize CSV exporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CSVExporter initialized with output directory: {self.output_dir}")
    
    def export_keywords(self, keywords: List[Keyword], filename: str = 'keywords.csv') -> Path:
        """
        Export keywords to CSV.
        
        Args:
            keywords: List of Keyword objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for kw in keywords:
            # Handle both old and new Keyword model structures
            # Check if keyword has direct attributes or uses metrics object
            if hasattr(kw, 'metrics') and kw.metrics:
                volume = kw.metrics.search_volume or 0
                cpc = kw.metrics.cpc or 0.0
                competition = kw.metrics.competition or 0.0
            else:
                # Fall back to direct attributes for backward compatibility
                volume = getattr(kw, 'volume', 0)
                cpc = getattr(kw, 'cpc', 0.0)
                competition = getattr(kw, 'competition', 0.0)
            
            data.append({
                'Keyword': kw.term,
                'Category': kw.category or '',
                'Volume': volume,
                'CPC': cpc,
                'Competition': competition,
                'Location': kw.location or '',
                'Intent': getattr(kw, 'intent', '') or '',
                'Difficulty': getattr(kw, 'difficulty', 0) or 0
            })
        
        return self._export_to_csv(data, filename, "keywords")
    
    def export_negative_keywords(self, negative_keywords: List[NegativeKeyword], 
                                filename: str = 'negative_keywords.csv') -> Path:
        """
        Export negative keywords to CSV.
        
        Args:
            negative_keywords: List of NegativeKeyword objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for neg in negative_keywords:
            data.append({
                'Negative Keyword': neg.term,
                'Match Type': neg.match_type or 'broad',
                'Reason': neg.reason or '',
                'Category': neg.category or ''
            })
        
        return self._export_to_csv(data, filename, "negative keywords")
    
    def export_ad_groups(self, ad_groups: List[AdGroup], filename: str = 'ad_groups.csv') -> Path:
        """
        Export ad groups to CSV in Google Ads format.
        
        Args:
            ad_groups: List of AdGroup objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        
        for ad_group in ad_groups:
            for keyword in ad_group.keywords:
                # Format keyword based on match type
                if ad_group.match_type == 'broad':
                    formatted_keyword = keyword
                elif ad_group.match_type == 'phrase':
                    formatted_keyword = f'"{keyword}"'
                elif ad_group.match_type == 'exact':
                    formatted_keyword = f'[{keyword}]'
                else:
                    formatted_keyword = keyword
                
                data.append({
                    'Campaign': ad_group.campaign_name or 'PPC Campaign',
                    'Ad Group': ad_group.name,
                    'Keyword': formatted_keyword,
                    'Match Type': ad_group.match_type.capitalize() if ad_group.match_type else 'Broad',
                    'Max CPC': ad_group.max_cpc or '',
                    'Status': 'Enabled'
                })
        
        return self._export_to_csv(data, filename, "ad groups")
    
    def export_competition_report(self, competitor_keywords: List[CompetitorKeyword], 
                                 filename: str = 'competition_report.csv') -> Path:
        """
        Export competition analysis to CSV.
        
        Args:
            competitor_keywords: List of CompetitorKeyword objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for kw in competitor_keywords:
            data.append({
                'Competitor': kw.competitor,
                'Keyword': kw.term,
                'Position': kw.position or '',
                'Volume': kw.volume or 0,
                'CPC': kw.cpc or 0.0,
                'Competition': kw.competition or 0.0,
                'Overlap': 'Yes' if kw.overlap else 'No',
                'Recommendation': kw.recommendation or ''
            })
        
        return self._export_to_csv(data, filename, "competition report")
    
    def export_competition_gaps(self, keyword_gaps: List[KeywordGap],
                               filename: str = 'keyword_gaps.csv') -> Path:
        """
        Export keyword gap analysis to CSV.
        
        Args:
            keyword_gaps: List of KeywordGap objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for gap in keyword_gaps:
            data.append({
                'Keyword': gap.keyword.term,
                'Gap Type': gap.gap_type,
                'Our Position': gap.our_position or 'Not Ranking',
                'Best Competitor Position': gap.best_competitor_position or '',
                'Competitor Domains': ', '.join(gap.competitor_domains) if gap.competitor_domains else '',
                'Search Volume': gap.keyword.metrics.search_volume if gap.keyword.metrics else 0,
                'CPC': gap.keyword.metrics.cpc if gap.keyword.metrics else 0,
                'Competition': gap.keyword.metrics.competition if gap.keyword.metrics else 0,
                'Priority': gap.priority,
                'Potential Traffic': gap.potential_traffic or 0,
                'Opportunity Score': f"{gap.calculate_opportunity_score():.2f}",
                'Recommendation': gap.recommendation
            })
        
        return self._export_to_csv(data, filename, "keyword gaps")
    
    def export_competitor_keywords(self, competitor_keywords: List[CompetitorKeyword],
                                  filename: str = 'competitor_keywords.csv') -> Path:
        """
        Export competitor keywords to CSV.
        
        Args:
            competitor_keywords: List of CompetitorKeyword objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for ck in competitor_keywords:
            data.append({
                'Keyword': ck.keyword.term,
                'Competitor Domain': ck.competitor_domain,
                'Position': ck.position or '',
                'Is Paid': 'Yes' if ck.is_paid else 'No',
                'Search Volume': ck.keyword.metrics.search_volume if ck.keyword.metrics else 0,
                'CPC': ck.keyword.metrics.cpc if ck.keyword.metrics else 0,
                'Competition': ck.keyword.metrics.competition if ck.keyword.metrics else 0,
                'Estimated Traffic': ck.estimated_traffic or 0,
                'Ad Copy': ck.ad_copy or '',
                'Landing Page': ck.landing_page or ''
            })
        
        return self._export_to_csv(data, filename, "competitor keywords")
    
    def export_scraped_copy(self, scraped_data: List[ScrapedCopy], 
                          filename: str = 'scraped_copy.csv') -> Path:
        """
        Export scraped landing page copy to CSV.
        
        Args:
            scraped_data: List of ScrapedCopy objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        for item in scraped_data:
            data.append({
                'URL': item.url,
                'Domain': item.domain or '',
                'Headline': item.headline or '',
                'Subheadline': item.subheadline or '',
                'Body Snippet': item.body_snippet or '',
                'CTA': item.cta or '',
                'Secondary CTAs': ', '.join(item.secondary_ctas) if item.secondary_ctas else '',
                'Features': ', '.join(item.features) if item.features else '',
                'Pricing': item.pricing or '',
                'Testimonials': ' | '.join(item.testimonials[:2]) if item.testimonials else '',
                'Meta Title': item.meta_title or '',
                'Meta Description': item.meta_description or '',
                'Scrape Success': 'Yes' if item.scrape_success else 'No'
            })
        
        return self._export_to_csv(data, filename, "scraped copy")
    
    def export_google_ads_import(self, ad_groups: List[AdGroup], 
                                negative_keywords: List[NegativeKeyword],
                                campaign_name: str = "PPC Campaign",
                                filename: str = 'google_ads_import.csv') -> Path:
        """
        Export data in Google Ads Editor format.
        
        Args:
            ad_groups: List of AdGroup objects
            negative_keywords: List of NegativeKeyword objects  
            campaign_name: Campaign name
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        data = []
        
        # Add campaign header
        data.append({
            'Campaign': campaign_name,
            'Campaign Status': 'Enabled',
            'Campaign Type': 'Search',
            'Campaign Budget': '',
            'Ad Group': '',
            'Max CPC': '',
            'Keyword': '',
            'Criterion Type': '',
            'Status': 'Enabled'
        })
        
        # Add ad groups and keywords
        for ad_group in ad_groups:
            # Add ad group header
            data.append({
                'Campaign': campaign_name,
                'Campaign Status': '',
                'Campaign Type': '',
                'Campaign Budget': '',
                'Ad Group': ad_group.name,
                'Max CPC': str(ad_group.max_cpc) if ad_group.max_cpc else '',
                'Keyword': '',
                'Criterion Type': '',
                'Status': 'Enabled'
            })
            
            # Add keywords for this ad group
            for keyword in ad_group.keywords:
                if ad_group.match_type == 'broad':
                    formatted_keyword = keyword
                elif ad_group.match_type == 'phrase':
                    formatted_keyword = f'"{keyword}"'
                elif ad_group.match_type == 'exact':
                    formatted_keyword = f'[{keyword}]'
                else:
                    formatted_keyword = keyword
                    
                data.append({
                    'Campaign': campaign_name,
                    'Campaign Status': '',
                    'Campaign Type': '',
                    'Campaign Budget': '',
                    'Ad Group': ad_group.name,
                    'Max CPC': '',
                    'Keyword': formatted_keyword,
                    'Criterion Type': 'Keyword',
                    'Status': 'Enabled'
                })
        
        # Add negative keywords
        for neg in negative_keywords:
            data.append({
                'Campaign': campaign_name,
                'Campaign Status': '',
                'Campaign Type': '',
                'Campaign Budget': '',
                'Ad Group': '',
                'Max CPC': '',
                'Keyword': neg.term,
                'Criterion Type': 'Negative Keyword',
                'Status': 'Enabled'
            })
        
        return self._export_to_csv(data, filename, "Google Ads import")
    
    def export_campaign_summary(self, 
                              keywords: List[Keyword],
                              ad_groups: List[AdGroup],
                              negative_keywords: List[NegativeKeyword],
                              filename: str = 'campaign_summary.csv') -> Path:
        """
        Export campaign summary statistics.
        
        Args:
            keywords: List of Keyword objects
            ad_groups: List of AdGroup objects
            negative_keywords: List of NegativeKeyword objects
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        total_volume = sum(kw.volume or 0 for kw in keywords)
        avg_cpc = sum(kw.cpc or 0 for kw in keywords) / len(keywords) if keywords else 0
        avg_competition = sum(kw.competition or 0 for kw in keywords) / len(keywords) if keywords else 0
        
        data = [{
            'Metric': 'Total Keywords',
            'Value': len(keywords)
        }, {
            'Metric': 'Total Ad Groups',
            'Value': len(ad_groups)
        }, {
            'Metric': 'Total Negative Keywords',
            'Value': len(negative_keywords)
        }, {
            'Metric': 'Total Search Volume',
            'Value': total_volume
        }, {
            'Metric': 'Average CPC',
            'Value': f'${avg_cpc:.2f}'
        }, {
            'Metric': 'Average Competition',
            'Value': f'{avg_competition:.2f}'
        }, {
            'Metric': 'Unique Locations',
            'Value': len(set(kw.location for kw in keywords if kw.location))
        }, {
            'Metric': 'Unique Categories',
            'Value': len(set(kw.category for kw in keywords if kw.category))
        }]
        
        return self._export_to_csv(data, filename, "campaign summary")
    
    def _export_to_csv(self, data: List[Dict[str, Any]], filename: str, data_type: str) -> Path:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename
            data_type: Type of data being exported (for logging)
            
        Returns:
            Path to exported file
            
        Raises:
            Exception: If export fails
        """
        try:
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = Path(filename).stem
            extension = Path(filename).suffix or '.csv'
            filename_with_timestamp = f"{base_name}_{timestamp}{extension}"
            filepath = self.output_dir / filename_with_timestamp
            
            # Convert to DataFrame and export
            if data:
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False, encoding='utf-8')
                logger.info(f"Exported {len(data)} {data_type} to {filepath}")
            else:
                # Create empty file with headers if no data
                with open(filepath, 'w') as f:
                    f.write("No data to export\n")
                logger.warning(f"No {data_type} to export, created empty file: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting {data_type} to CSV: {e}")
            raise