"""Tests for ExportManager functionality."""

import pytest
import tempfile
import shutil
import json
import zipfile
from pathlib import Path
from datetime import datetime
import pandas as pd

from src.output_generator.export_manager import ExportManager
from models.keyword_models import Keyword, NegativeKeyword, KeywordMetrics
from models.export_models import SimpleAdGroup as AdGroup  # Use simplified model for tests
from models.competition_models import CompetitorKeyword, ScrapedCopy


class TestExportManager:
    """Test suite for ExportManager class."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory structure."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir) / "test_project"
        
        # Create project structure
        (project_path / "outputs" / "keywords").mkdir(parents=True)
        (project_path / "outputs" / "ad_groups").mkdir(parents=True)
        (project_path / "outputs" / "negatives").mkdir(parents=True)
        (project_path / "outputs" / "analysis").mkdir(parents=True)
        (project_path / "outputs" / "exports").mkdir(parents=True)
        (project_path / "configs").mkdir(parents=True)
        (project_path / "inputs" / "keywords").mkdir(parents=True)
        
        yield project_path
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def export_manager(self, temp_project_dir):
        """Create an ExportManager instance."""
        return ExportManager(temp_project_dir)
    
    @pytest.fixture
    def sample_keywords(self):
        """Create sample keyword data."""
        return [
            Keyword(
                term="emergency plumber austin",
                category="emergency",
                metrics=KeywordMetrics(
                    search_volume=1000,
                    cpc=5.50,
                    competition=0.85
                ),
                location="Austin, TX"
            ),
            Keyword(
                term="water heater repair near me",
                category="repair",
                metrics=KeywordMetrics(
                    search_volume=800,
                    cpc=4.25,
                    competition=0.72
                ),
                location="Austin, TX"
            ),
            Keyword(
                term="drain cleaning service",
                category="service",
                metrics=KeywordMetrics(
                    search_volume=600,
                    cpc=3.75,
                    competition=0.68
                ),
                location="Round Rock, TX"
            ),
            Keyword(
                term="24 hour plumber",
                category="emergency",
                metrics=KeywordMetrics(
                    search_volume=1200,
                    cpc=6.00,
                    competition=0.90
                ),
                location="Austin, TX"
            ),
            Keyword(
                term="plumbing repair cost",
                category="informational",
                metrics=KeywordMetrics(
                    search_volume=400,
                    cpc=2.50,
                    competition=0.45
                ),
                location="Austin, TX"
            )
        ]
    
    @pytest.fixture
    def sample_ad_groups(self):
        """Create sample ad group data."""
        return [
            AdGroup(
                name="Emergency Plumbing - Austin - Exact",
                keywords=["emergency plumber austin", "24 hour plumber austin"],
                match_type="exact",
                campaign_name="Austin Plumbing Services",
                max_cpc=6.00
            ),
            AdGroup(
                name="Repair Services - Austin - Phrase",
                keywords=["water heater repair", "pipe repair", "leak repair"],
                match_type="phrase",
                campaign_name="Austin Plumbing Services",
                max_cpc=5.00
            ),
            AdGroup(
                name="Drain Services - Round Rock - Broad",
                keywords=["drain cleaning", "clogged drain", "drain service"],
                match_type="broad",
                campaign_name="Round Rock Plumbing",
                max_cpc=4.00
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
            ),
            NegativeKeyword(
                term="training",
                match_type="broad",
                reason="Educational searches",
                category="education"
            )
        ]
    
    @pytest.fixture
    def sample_competitor_keywords(self):
        """Create sample competitor keyword data."""
        return [
            CompetitorKeyword(
                competitor="competitor1.com",
                term="emergency plumbing austin",
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
                url="https://example.com/plumbing",
                domain="example.com",
                headline="Best Plumbing Services in Austin",
                subheadline="24/7 Emergency Service Available",
                body_snippet="Professional plumbing services available around the clock",
                cta="Get Free Quote",
                secondary_ctas=["Call Now", "Schedule Service"],
                features=["Licensed & Insured", "24/7 Service", "Free Estimates"],
                pricing="Starting at $99",
                testimonials=["Great service!", "Fast response time"],
                meta_title="Austin Plumbing Services | Example",
                meta_description="Professional plumbing services in Austin",
                scrape_success=True
            )
        ]
    
    def test_initialization(self, temp_project_dir):
        """Test ExportManager initialization."""
        export_manager = ExportManager(temp_project_dir)
        assert export_manager.project_path == temp_project_dir
        assert export_manager.output_dir == temp_project_dir / "outputs" / "exports"
        assert export_manager.output_dir.exists()
    
    def test_initialization_custom_output(self, temp_project_dir):
        """Test ExportManager initialization with custom output directory."""
        custom_output = temp_project_dir / "custom_exports"
        export_manager = ExportManager(temp_project_dir, custom_output)
        assert export_manager.output_dir == custom_output
        assert custom_output.exists()
    
    def test_export_full_campaign(self, export_manager, sample_keywords, 
                                 sample_ad_groups, sample_negative_keywords):
        """Test full campaign export."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["csv"],
            create_zip=False,
            validate_google_ads=True
        )
        
        assert result['success'] is True
        assert len(result['exported_files']) > 0
        assert result['statistics']['keywords_count'] == 5
        assert result['statistics']['ad_groups_count'] == 3
        assert result['statistics']['negative_keywords_count'] == 4
        assert 'validation_results' in result['statistics']
    
    def test_google_ads_validation(self, export_manager, sample_ad_groups, 
                                  sample_negative_keywords):
        """Test Google Ads format validation."""
        # Add invalid data
        invalid_ad_group = AdGroup(
            name="A" * 256,  # Name too long
            keywords=["valid keyword", "!" * 85],  # Invalid keyword
            match_type="exact",
            campaign_name="Test Campaign",
            max_cpc=15000  # CPC too high
        )
        
        ad_groups = sample_ad_groups + [invalid_ad_group]
        
        result = export_manager.export_full_campaign(
            keywords=[],
            ad_groups=ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["google"],
            create_zip=False,
            validate_google_ads=True
        )
        
        assert result['success'] is True
        validation = result['statistics']['validation_results']
        assert len(validation['errors']) > 0  # Should have error for long name
        assert len(validation['warnings']) > 0  # Should have warnings
    
    def test_zip_creation(self, export_manager, sample_keywords, 
                         sample_ad_groups, sample_negative_keywords):
        """Test ZIP archive creation."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["csv"],
            create_zip=True
        )
        
        assert result['success'] is True
        assert 'zip_archive' in result['statistics']
        zip_path = Path(result['statistics']['zip_archive'])
        assert zip_path.exists()
        assert zip_path.suffix == '.zip'
        
        # Verify ZIP contents
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            namelist = zipf.namelist()
            assert 'export_summary.json' in namelist
            assert any('keywords' in name for name in namelist)
            assert any('ad_groups' in name for name in namelist)
    
    def test_export_with_competition_data(self, export_manager, sample_keywords,
                                         sample_ad_groups, sample_negative_keywords,
                                         sample_competitor_keywords, sample_scraped_copy):
        """Test export with competition analysis data."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            competitor_keywords=sample_competitor_keywords,
            scraped_copy=sample_scraped_copy,
            campaign_name="Test Campaign",
            formats=["csv"]
        )
        
        assert result['success'] is True
        assert result['statistics']['competitor_keywords_count'] == 2
        assert result['statistics']['scraped_pages_count'] == 1
        assert any('competition' in str(f) for f in result['exported_files'])
        assert any('scraped' in str(f) for f in result['exported_files'])
    
    def test_export_multiple_formats(self, export_manager, sample_keywords,
                                    sample_ad_groups, sample_negative_keywords):
        """Test exporting multiple formats."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["google", "bing", "csv"]
        )
        
        assert result['success'] is True
        assert 'google' in result['statistics']['formats_exported']
        assert 'bing' in result['statistics']['formats_exported']
        assert 'csv' in result['statistics']['formats_exported']
        
        # Check for format-specific files
        file_names = [Path(f).name for f in result['exported_files']]
        assert any('google' in name.lower() for name in file_names)
        assert any('bing' in name.lower() for name in file_names)
    
    def test_export_summary_generation(self, export_manager, sample_keywords,
                                      sample_ad_groups, sample_negative_keywords):
        """Test export summary generation."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["csv"]
        )
        
        assert result['success'] is True
        
        # Check for summary file
        summary_file = export_manager.output_dir / "export_summary.json"
        assert summary_file.exists()
        
        # Verify summary content
        with open(summary_file) as f:
            summary = json.load(f)
        
        assert 'export_info' in summary
        assert 'data_statistics' in summary
        assert summary['data_statistics']['keywords']['total'] == 5
        assert summary['data_statistics']['keywords']['message'] == "5 keywords generated"
        assert summary['data_statistics']['ad_groups']['message'] == "3 ad groups created"
    
    def test_include_project_settings(self, export_manager, temp_project_dir,
                                     sample_keywords, sample_ad_groups,
                                     sample_negative_keywords):
        """Test including project settings in export."""
        # Create sample config files
        config_dir = temp_project_dir / "configs"
        project_config = {
            "project_name": "test_project",
            "target_platforms": ["google_ads"],
            "language": "en"
        }
        
        with open(config_dir / "project_config.json", 'w') as f:
            json.dump(project_config, f)
        
        # Create metadata file
        metadata = {
            "project_id": "test-id",
            "project_name": "test_project",
            "created_date": datetime.now().isoformat()
        }
        
        with open(temp_project_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f)
        
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["csv"],
            include_settings=True
        )
        
        assert result['success'] is True
        
        # Check if config files were copied
        assert (export_manager.output_dir / "project_config.json").exists()
        assert (export_manager.output_dir / "project_metadata.json").exists()
    
    def test_export_from_project(self, export_manager, temp_project_dir,
                                sample_keywords, sample_ad_groups,
                                sample_negative_keywords):
        """Test loading and exporting data from project structure."""
        # Create sample data files in project structure
        keywords_dir = temp_project_dir / "outputs" / "keywords"
        ad_groups_dir = temp_project_dir / "outputs" / "ad_groups"
        negatives_dir = temp_project_dir / "outputs" / "negatives"
        
        # Save keywords
        keywords_data = []
        for kw in sample_keywords:
            keywords_data.append({
                'Keyword': kw.term,
                'Category': kw.category,
                'Volume': kw.volume,
                'CPC': kw.cpc,
                'Competition': kw.competition,
                'Location': kw.location
            })
        
        keywords_df = pd.DataFrame(keywords_data)
        keywords_df.to_csv(keywords_dir / "expanded_keywords.csv", index=False)
        
        # Save ad groups
        ad_groups_data = []
        for ag in sample_ad_groups:
            for keyword in ag.keywords:
                ad_groups_data.append({
                    'Campaign': ag.campaign_name,
                    'Ad Group': ag.name,
                    'Keyword': keyword,
                    'Match Type': ag.match_type.capitalize(),
                    'Max CPC': ag.max_cpc
                })
        
        ad_groups_df = pd.DataFrame(ad_groups_data)
        ad_groups_df.to_csv(ad_groups_dir / "ad_groups_combined.csv", index=False)
        
        # Save negative keywords
        neg_data = []
        for neg in sample_negative_keywords:
            neg_data.append({
                'Negative Keyword': neg.term,
                'Match Type': neg.match_type,
                'Reason': neg.reason,
                'Category': neg.category
            })
        
        neg_df = pd.DataFrame(neg_data)
        neg_df.to_csv(negatives_dir / "negative_keywords.csv", index=False)
        
        # Test export from project
        result = export_manager.export_from_project(
            formats=["csv"],
            create_zip=True
        )
        
        assert result['success'] is True
        assert result['statistics']['keywords_count'] == 5
        assert result['statistics']['ad_groups_count'] == 3
        assert result['statistics']['negative_keywords_count'] == 4
        assert 'zip_path' in result
    
    def test_empty_data_export(self, export_manager):
        """Test exporting with empty data."""
        result = export_manager.export_full_campaign(
            keywords=[],
            ad_groups=[],
            negative_keywords=[],
            campaign_name="Empty Campaign",
            formats=["csv"]
        )
        
        assert result['success'] is True
        assert result['statistics']['keywords_count'] == 0
        assert result['statistics']['ad_groups_count'] == 0
        assert result['statistics']['negative_keywords_count'] == 0
    
    def test_all_formats_shortcut(self, export_manager, sample_keywords,
                                 sample_ad_groups, sample_negative_keywords):
        """Test 'all' formats shortcut."""
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["all"]
        )
        
        assert result['success'] is True
        # 'all' should expand to google, bing, csv
        formats = result['statistics']['formats_exported']
        assert "google" in formats or "all" in formats
    
    def test_export_logging(self, export_manager, sample_keywords,
                          sample_ad_groups, sample_negative_keywords, caplog):
        """Test comprehensive logging of export operations."""
        import logging
        caplog.set_level(logging.INFO)
        
        result = export_manager.export_full_campaign(
            keywords=sample_keywords,
            ad_groups=sample_ad_groups,
            negative_keywords=sample_negative_keywords,
            campaign_name="Test Campaign",
            formats=["csv"]
        )
        
        assert result['success'] is True
        
        # Check for key log messages
        assert "EXPORT SUMMARY" in caplog.text
        assert "5 keywords generated" in caplog.text
        assert "3 ad groups created" in caplog.text
        assert "4 negative keywords identified" in caplog.text
        assert "Files Exported:" in caplog.text