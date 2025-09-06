"""Tests for CSV exporter functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime

from src.output_generator.csv_exporter import CSVExporter
from models.keyword_models import Keyword, NegativeKeyword
from models.ad_group_models import AdGroup
from models.competition_models import CompetitorKeyword, ScrapedCopy


class TestCSVExporter:
    """Test suite for CSVExporter class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def csv_exporter(self, temp_dir):
        """Create a CSVExporter instance with temporary directory."""
        return CSVExporter(output_dir=str(temp_dir))
    
    @pytest.fixture
    def sample_keywords(self):
        """Create sample keyword data."""
        return [
            Keyword(
                term="emergency plumber",
                category="emergency",
                volume=1000,
                cpc=5.50,
                competition=0.85,
                location="Austin, TX",
                intent="commercial",
                difficulty=65
            ),
            Keyword(
                term="water heater repair",
                category="repair",
                volume=500,
                cpc=4.25,
                competition=0.72,
                location="Austin, TX",
                intent="commercial",
                difficulty=58
            ),
            Keyword(
                term="drain cleaning service",
                category="service",
                volume=300,
                cpc=3.75,
                competition=0.68,
                location="Round Rock, TX",
                intent="commercial",
                difficulty=52
            )
        ]
    
    @pytest.fixture
    def sample_negative_keywords(self):
        """Create sample negative keyword data."""
        return [
            NegativeKeyword(
                term="free",
                match_type="broad",
                reason="No monetization potential",
                category="general"
            ),
            NegativeKeyword(
                term="diy",
                match_type="phrase",
                reason="Do-it-yourself searches",
                category="general"
            ),
            NegativeKeyword(
                term="jobs",
                match_type="exact",
                reason="Job seekers",
                category="employment"
            )
        ]
    
    @pytest.fixture
    def sample_ad_groups(self):
        """Create sample ad group data."""
        return [
            AdGroup(
                name="Emergency Services - Austin - Exact",
                keywords=["emergency plumber", "24 hour plumber"],
                match_type="exact",
                campaign_name="Plumbing Services",
                max_cpc=6.00
            ),
            AdGroup(
                name="Repair Services - Austin - Phrase",
                keywords=["water heater repair", "pipe repair"],
                match_type="phrase",
                campaign_name="Plumbing Services",
                max_cpc=5.00
            ),
            AdGroup(
                name="Drain Services - Round Rock - Broad",
                keywords=["drain cleaning", "clogged drain"],
                match_type="broad",
                campaign_name="Plumbing Services",
                max_cpc=4.00
            )
        ]
    
    @pytest.fixture
    def sample_competitor_keywords(self):
        """Create sample competitor keyword data."""
        return [
            CompetitorKeyword(
                competitor="competitor1.com",
                term="emergency plumbing",
                position=1,
                volume=1500,
                cpc=6.00,
                competition=0.90,
                overlap=True,
                recommendation="Target with higher bid"
            ),
            CompetitorKeyword(
                competitor="competitor2.com",
                term="plumber near me",
                position=3,
                volume=2000,
                cpc=4.50,
                competition=0.75,
                overlap=False,
                recommendation="Add to campaign"
            )
        ]
    
    @pytest.fixture
    def sample_scraped_copy(self):
        """Create sample scraped copy data."""
        return [
            ScrapedCopy(
                url="https://example.com",
                domain="example.com",
                headline="Best Plumbing Services",
                subheadline="24/7 Emergency Service",
                body_snippet="Professional plumbing services available around the clock",
                cta="Get Free Quote",
                secondary_ctas=["Call Now", "Schedule Service"],
                features=["Licensed", "Insured", "24/7 Service"],
                pricing="Starting at $99",
                testimonials=["Great service!", "Fast response"],
                meta_title="Plumbing Services | Example",
                meta_description="Professional plumbing services",
                scrape_success=True
            )
        ]
    
    def test_initialization(self, temp_dir):
        """Test CSVExporter initialization."""
        exporter = CSVExporter(output_dir=str(temp_dir))
        assert exporter.output_dir == temp_dir
        assert temp_dir.exists()
    
    def test_export_keywords(self, csv_exporter, sample_keywords):
        """Test exporting keywords to CSV."""
        filepath = csv_exporter.export_keywords(sample_keywords)
        
        assert filepath.exists()
        assert filepath.suffix == '.csv'
        
        # Read and verify content
        df = pd.read_csv(filepath)
        assert len(df) == 3
        assert 'Keyword' in df.columns
        assert 'Volume' in df.columns
        assert 'CPC' in df.columns
        assert df.iloc[0]['Keyword'] == 'emergency plumber'
        assert df.iloc[0]['Volume'] == 1000
        assert df.iloc[0]['CPC'] == 5.50
    
    def test_export_negative_keywords(self, csv_exporter, sample_negative_keywords):
        """Test exporting negative keywords to CSV."""
        filepath = csv_exporter.export_negative_keywords(sample_negative_keywords)
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert len(df) == 3
        assert 'Negative Keyword' in df.columns
        assert 'Match Type' in df.columns
        assert 'Reason' in df.columns
        assert df.iloc[0]['Negative Keyword'] == 'free'
        assert df.iloc[1]['Match Type'] == 'phrase'
    
    def test_export_ad_groups(self, csv_exporter, sample_ad_groups):
        """Test exporting ad groups to CSV."""
        filepath = csv_exporter.export_ad_groups(sample_ad_groups)
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert len(df) == 6  # 3 ad groups x 2 keywords each
        assert 'Ad Group' in df.columns
        assert 'Keyword' in df.columns
        assert 'Match Type' in df.columns
        
        # Check keyword formatting
        exact_keywords = df[df['Ad Group'].str.contains('Exact')]['Keyword'].values
        assert all(k.startswith('[') and k.endswith(']') for k in exact_keywords)
        
        phrase_keywords = df[df['Ad Group'].str.contains('Phrase')]['Keyword'].values
        assert all(k.startswith('"') and k.endswith('"') for k in phrase_keywords)
        
        broad_keywords = df[df['Ad Group'].str.contains('Broad')]['Keyword'].values
        assert not any(k.startswith('[') or k.startswith('"') for k in broad_keywords)
    
    def test_export_competition_report(self, csv_exporter, sample_competitor_keywords):
        """Test exporting competition report to CSV."""
        filepath = csv_exporter.export_competition_report(sample_competitor_keywords)
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert len(df) == 2
        assert 'Competitor' in df.columns
        assert 'Keyword' in df.columns
        assert 'Position' in df.columns
        assert 'Overlap' in df.columns
        assert df.iloc[0]['Competitor'] == 'competitor1.com'
        assert df.iloc[0]['Overlap'] == 'Yes'
        assert df.iloc[1]['Overlap'] == 'No'
    
    def test_export_scraped_copy(self, csv_exporter, sample_scraped_copy):
        """Test exporting scraped copy to CSV."""
        filepath = csv_exporter.export_scraped_copy(sample_scraped_copy)
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert len(df) == 1
        assert 'URL' in df.columns
        assert 'Headline' in df.columns
        assert 'CTA' in df.columns
        assert 'Features' in df.columns
        assert df.iloc[0]['URL'] == 'https://example.com'
        assert df.iloc[0]['Headline'] == 'Best Plumbing Services'
        assert 'Call Now' in df.iloc[0]['Secondary CTAs']
    
    def test_export_google_ads_import(self, csv_exporter, sample_ad_groups, sample_negative_keywords):
        """Test exporting Google Ads import format."""
        filepath = csv_exporter.export_google_ads_import(
            sample_ad_groups,
            sample_negative_keywords,
            campaign_name="Test Campaign"
        )
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert 'Campaign' in df.columns
        assert 'Ad Group' in df.columns
        assert 'Keyword' in df.columns
        assert 'Criterion Type' in df.columns
        
        # Check campaign header
        assert df.iloc[0]['Campaign'] == 'Test Campaign'
        assert df.iloc[0]['Campaign Status'] == 'Enabled'
        
        # Check for negative keywords
        neg_rows = df[df['Criterion Type'] == 'Negative Keyword']
        assert len(neg_rows) == 3
    
    def test_export_campaign_summary(self, csv_exporter, sample_keywords, 
                                    sample_ad_groups, sample_negative_keywords):
        """Test exporting campaign summary."""
        filepath = csv_exporter.export_campaign_summary(
            sample_keywords,
            sample_ad_groups,
            sample_negative_keywords
        )
        
        assert filepath.exists()
        
        df = pd.read_csv(filepath)
        assert 'Metric' in df.columns
        assert 'Value' in df.columns
        
        # Check metrics
        metrics = df.set_index('Metric')['Value'].to_dict()
        assert metrics['Total Keywords'] == 3
        assert metrics['Total Ad Groups'] == 3
        assert metrics['Total Negative Keywords'] == 3
        assert metrics['Total Search Volume'] == 1800
    
    def test_empty_data_export(self, csv_exporter):
        """Test exporting empty data."""
        filepath = csv_exporter.export_keywords([])
        
        assert filepath.exists()
        
        # Check that file contains message about no data
        with open(filepath, 'r') as f:
            content = f.read()
            assert "No data" in content
    
    def test_filename_with_timestamp(self, csv_exporter, sample_keywords):
        """Test that exported files have timestamp."""
        filepath = csv_exporter.export_keywords(sample_keywords, "test_keywords.csv")
        
        filename = filepath.name
        assert "test_keywords_" in filename
        assert filename.endswith('.csv')
        
        # Check timestamp format (YYYYMMDD_HHMMSS)
        parts = filename.replace('.csv', '').split('_')
        timestamp_parts = parts[-2:]  # Last two parts should be date and time
        assert len(timestamp_parts[0]) == 8  # YYYYMMDD
        assert len(timestamp_parts[1]) == 6  # HHMMSS
    
    def test_export_error_handling(self, temp_dir):
        """Test error handling in export."""
        # Create exporter with invalid directory
        exporter = CSVExporter(output_dir="/invalid/path/that/does/not/exist")
        
        # This should still work as directory is created
        assert exporter.output_dir.exists()
    
    def test_unicode_handling(self, csv_exporter):
        """Test handling of unicode characters."""
        keywords = [
            Keyword(
                term="plombier d'urgence",  # French
                category="urgence",
                location="Montréal, QC"
            ),
            Keyword(
                term="配管工",  # Japanese
                category="サービス",
                location="東京"
            )
        ]
        
        filepath = csv_exporter.export_keywords(keywords)
        assert filepath.exists()
        
        # Read and verify unicode is preserved
        df = pd.read_csv(filepath, encoding='utf-8')
        assert df.iloc[0]['Keyword'] == "plombier d'urgence"
        assert df.iloc[1]['Keyword'] == "配管工"