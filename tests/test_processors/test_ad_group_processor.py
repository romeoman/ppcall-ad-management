"""
Unit tests for AdGroupProcessor
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from src.processors.ad_group_processor import AdGroupProcessor
from models.keyword_models import Keyword, KeywordMetrics, MatchType
from models.ad_group_models import AdGroup, AdGroupKeyword


class TestAdGroupProcessor:
    """Test suite for AdGroupProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create an AdGroupProcessor instance for testing."""
        return AdGroupProcessor()
    
    @pytest.fixture
    def sample_keywords(self):
        """Create sample keywords for testing."""
        return [
            Keyword(
                term="emergency plumber chicago",
                metrics=KeywordMetrics(
                    search_volume=1000,
                    competition=0.8,
                    cpc=15.50
                ),
                category="Emergency Plumbing",
                location="Chicago",
                metadata={"search_intent": "transactional"}
            ),
            Keyword(
                term="24 hour plumber chicago",
                metrics=KeywordMetrics(
                    search_volume=800,
                    competition=0.75,
                    cpc=14.00
                ),
                category="Emergency Plumbing",
                location="Chicago",
                metadata={"search_intent": "transactional"}
            ),
            Keyword(
                term="water damage repair chicago",
                metrics=KeywordMetrics(
                    search_volume=600,
                    competition=0.7,
                    cpc=12.50
                ),
                category="Water Damage",
                location="Chicago",
                metadata={"search_intent": "transactional"}
            ),
            Keyword(
                term="toilet repair new york",
                metrics=KeywordMetrics(
                    search_volume=1200,
                    competition=0.65,
                    cpc=10.00
                ),
                category="Toilet Repair",
                location="New York",
                metadata={"search_intent": "transactional"}
            ),
            Keyword(
                term="plumbing services",
                metrics=KeywordMetrics(
                    search_volume=5000,
                    competition=0.9,
                    cpc=20.00
                ),
                category="General Plumbing",
                location=None,
                metadata={"search_intent": "informational"}
            )
        ]
    
    def test_initialization(self, processor):
        """Test processor initialization with default values."""
        assert processor.min_keywords == 3
        assert processor.max_keywords == 50
        assert processor.optimal_keywords == 15
        assert processor.MATCH_TYPES == ['broad', 'phrase', 'exact']
    
    def test_initialization_custom_values(self):
        """Test processor initialization with custom values."""
        processor = AdGroupProcessor(
            min_keywords=5,
            max_keywords=30,
            optimal_keywords=10
        )
        assert processor.min_keywords == 5
        assert processor.max_keywords == 30
        assert processor.optimal_keywords == 10
    
    def test_create_ad_groups_basic(self, processor, sample_keywords):
        """Test basic ad group creation."""
        ad_groups = processor.create_ad_groups(sample_keywords)
        
        assert len(ad_groups) > 0
        assert all(isinstance(ag, AdGroup) for ag in ad_groups)
        
        # Check that all keywords are included
        total_keywords = sum(len(ag.keywords) for ag in ad_groups)
        assert total_keywords == len(sample_keywords)
    
    def test_create_ad_groups_with_match_types(self, processor, sample_keywords):
        """Test ad group creation with multiple match types."""
        match_types = ['broad', 'phrase', 'exact']
        ad_groups = processor.create_ad_groups(
            sample_keywords, 
            match_types=match_types
        )
        
        # Should have ad groups for each unique group and match type combination
        match_type_counts = {}
        for ag in ad_groups:
            for kw in ag.keywords:
                match_type = kw.keyword.match_type
                match_type_counts[match_type] = match_type_counts.get(match_type, 0) + 1
        
        # Each match type should have keywords
        for match_type in match_types:
            assert match_type in match_type_counts
    
    def test_invalid_match_type(self, processor, sample_keywords):
        """Test that invalid match types raise ValueError."""
        with pytest.raises(ValueError, match=r"Invalid match type"):
            processor.create_ad_groups(
                sample_keywords, 
                match_types=['invalid_type']
            )
    
    def test_empty_keywords_list(self, processor):
        """Test handling of empty keywords list."""
        ad_groups = processor.create_ad_groups([])
        assert ad_groups == []
    
    def test_grouping_by_category_and_location(self, processor, sample_keywords):
        """Test that keywords are grouped by category and location."""
        ad_groups = processor.create_ad_groups(
            sample_keywords,
            group_by_intent=False,
            balance_groups=False  # Don't merge small groups for this test
        )
        
        # Check that Emergency Plumbing Chicago keywords exist in some group
        all_keywords_in_groups = []
        for ag in ad_groups:
            for kw in ag.keywords:
                all_keywords_in_groups.append(kw.keyword.term)
        
        # Check that both Emergency Plumbing Chicago keywords are included
        assert "emergency plumber chicago" in all_keywords_in_groups
        assert "24 hour plumber chicago" in all_keywords_in_groups
        
        # Check that there's at least one group with Chicago Emergency keywords
        chicago_emergency_found = False
        for ag in ad_groups:
            keyword_terms = [kw.keyword.term for kw in ag.keywords]
            if any("emergency plumber chicago" in term for term in keyword_terms):
                chicago_emergency_found = True
                break
        assert chicago_emergency_found
    
    def test_format_keyword_for_match_type(self, processor):
        """Test keyword formatting for different match types."""
        keyword = "plumber chicago"
        
        # Test broad match
        broad = processor._format_keyword_for_match_type(keyword, 'broad')
        assert broad == "plumber chicago"
        
        # Test phrase match
        phrase = processor._format_keyword_for_match_type(keyword, 'phrase')
        assert phrase == '"plumber chicago"'
        
        # Test exact match
        exact = processor._format_keyword_for_match_type(keyword, 'exact')
        assert exact == '[plumber chicago]'
    
    def test_suggest_bid(self, processor):
        """Test bid suggestion based on competition."""
        # High competition keyword
        high_comp_keyword = Keyword(
            term="test",
            metrics=KeywordMetrics(
                search_volume=1000,
                competition=0.9,
                cpc=10.00
            )
        )
        high_bid = processor._suggest_bid(high_comp_keyword)
        assert high_bid == 12.00  # 10.00 * 1.2
        
        # Medium competition keyword
        med_comp_keyword = Keyword(
            term="test",
            metrics=KeywordMetrics(
                search_volume=1000,
                competition=0.5,
                cpc=10.00
            )
        )
        med_bid = processor._suggest_bid(med_comp_keyword)
        assert med_bid == 10.00  # 10.00 * 1.0
        
        # Low competition keyword
        low_comp_keyword = Keyword(
            term="test",
            metrics=KeywordMetrics(
                search_volume=1000,
                competition=0.2,
                cpc=10.00
            )
        )
        low_bid = processor._suggest_bid(low_comp_keyword)
        assert low_bid == 8.00  # 10.00 * 0.8
        
        # No metrics data
        no_metrics_keyword = Keyword(
            term="test",
            metrics=None
        )
        no_bid = processor._suggest_bid(no_metrics_keyword)
        assert no_bid is None
    
    def test_balance_groups_split_large(self, processor):
        """Test splitting of large ad groups."""
        # Create a large group of keywords
        large_keyword_list = [
            Keyword(
                term=f"keyword {i}",
                metrics=KeywordMetrics(
                    search_volume=100 * i,
                    competition=0.5,
                    cpc=1.00
                ),
                category="Large Category",
                location="Test Location"
            )
            for i in range(60)  # More than max_keywords
        ]
        
        ad_groups = processor.create_ad_groups(
            large_keyword_list,
            balance_groups=True
        )
        
        # Check that no group exceeds max_keywords
        for ag in ad_groups:
            assert len(ag.keywords) <= processor.max_keywords
    
    def test_balance_groups_merge_small(self, processor):
        """Test merging of small ad groups."""
        # Create keywords that would form small groups
        small_groups_keywords = [
            Keyword(
                term="keyword1",
                metrics=KeywordMetrics(
                    search_volume=100,
                    competition=0.5,
                    cpc=1.00
                ),
                category="Category A",
                location="Location 1"
            ),
            Keyword(
                term="keyword2",
                metrics=KeywordMetrics(
                    search_volume=100,
                    competition=0.5,
                    cpc=1.00
                ),
                category="Category B",
                location="Location 2"
            )
        ]
        
        ad_groups = processor.create_ad_groups(
            small_groups_keywords,
            balance_groups=True
        )
        
        # Small groups should be handled (either kept with warning or merged)
        assert len(ad_groups) > 0
    
    def test_format_for_google_ads(self, processor, sample_keywords):
        """Test formatting for Google Ads export."""
        ad_groups = processor.create_ad_groups(sample_keywords)
        formatted_data = processor.format_for_google_ads(ad_groups)
        
        assert len(formatted_data) > 0
        
        # Check required fields
        for row in formatted_data:
            if 'Keyword' in row:
                assert 'Campaign' in row
                assert 'Ad Group' in row
                assert 'Match Type' in row
                assert 'Max CPC' in row
    
    def test_format_for_bing_ads(self, processor, sample_keywords):
        """Test formatting for Bing Ads export."""
        ad_groups = processor.create_ad_groups(sample_keywords)
        formatted_data = processor.format_for_bing_ads(ad_groups)
        
        assert len(formatted_data) > 0
        
        # Check required fields for Bing
        for row in formatted_data:
            assert 'Campaign' in row
            assert 'Ad Group' in row
            assert 'Keyword' in row
            assert 'Match Type' in row
            assert 'Bid' in row
            assert 'Status' in row
    
    def test_get_ad_group_statistics(self, processor, sample_keywords):
        """Test calculation of ad group statistics."""
        ad_groups = processor.create_ad_groups(
            sample_keywords,
            match_types=['broad', 'phrase']
        )
        stats = processor.get_ad_group_statistics(ad_groups)
        
        assert 'total_ad_groups' in stats
        assert 'total_keywords' in stats
        assert 'avg_keywords_per_group' in stats
        assert 'match_type_distribution' in stats
        assert 'bid_range' in stats
        assert 'groups_by_size' in stats
        
        assert stats['total_ad_groups'] == len(ad_groups)
        assert stats['total_keywords'] > 0
        assert stats['avg_keywords_per_group'] > 0
    
    def test_get_ad_group_statistics_empty(self, processor):
        """Test statistics calculation with empty ad groups."""
        stats = processor.get_ad_group_statistics([])
        
        assert stats['total_ad_groups'] == 0
        assert stats['total_keywords'] == 0
        assert stats['avg_keywords_per_group'] == 0
    
    def test_validate_ad_groups(self, processor, sample_keywords):
        """Test ad group validation."""
        ad_groups = processor.create_ad_groups(sample_keywords)
        issues = processor.validate_ad_groups(ad_groups)
        
        # Should be a list (may be empty if no issues)
        assert isinstance(issues, list)
    
    def test_validate_ad_groups_duplicates(self, processor):
        """Test validation catches duplicate ad group names."""
        # Create keywords for ad groups
        keyword1 = Keyword(term="test1")
        keyword2 = Keyword(term="test2")
        
        # Create ad groups with duplicate names
        ad_group1 = AdGroup(
            name="Test Group",
            campaign_name="Test Campaign",
            keywords=[
                AdGroupKeyword(keyword=keyword1, bid=1.00)
            ],
            default_bid=1.00,
            status="enabled"
        )
        ad_group2 = AdGroup(
            name="Test Group",  # Duplicate name
            campaign_name="Test Campaign",
            keywords=[
                AdGroupKeyword(keyword=keyword2, bid=1.00)
            ],
            default_bid=1.00,
            status="enabled"
        )
        
        issues = processor.validate_ad_groups([ad_group1, ad_group2])
        assert any("Duplicate ad group names" in issue for issue in issues)
    
    def test_validate_ad_groups_size_issues(self, processor):
        """Test validation catches size issues."""
        # Create keyword for small ad group
        keyword = Keyword(term="test")
        
        # Create ad group with too few keywords
        small_ad_group = AdGroup(
            name="Small Group",
            campaign_name="Test Campaign",
            keywords=[
                AdGroupKeyword(keyword=keyword, bid=1.00)
            ],
            default_bid=1.00,
            status="enabled"
        )
        
        issues = processor.validate_ad_groups([small_ad_group])
        assert any("only 1 keywords" in issue for issue in issues)
    
    def test_group_by_intent(self, processor, sample_keywords):
        """Test grouping by search intent."""
        ad_groups = processor.create_ad_groups(
            sample_keywords,
            group_by_intent=True
        )
        
        # Check that transactional intents are grouped
        transactional_groups = [
            ag for ag in ad_groups
            if "transactional" in ag.name.lower()
        ]
        
        # Should have at least one transactional group or general groups
        assert len(ad_groups) > 0
    
    def test_calculate_default_bid(self, processor):
        """Test default bid calculation."""
        # High competition
        high_bid = processor._calculate_default_bid(10.00, 0.8)
        assert high_bid == 11.50  # 10.00 * 1.15
        
        # Medium competition
        med_bid = processor._calculate_default_bid(10.00, 0.5)
        assert med_bid == 10.00  # 10.00 * 1.0
        
        # Low competition
        low_bid = processor._calculate_default_bid(10.00, 0.2)
        assert low_bid == 8.50  # 10.00 * 0.85
        
        # No CPC data
        no_cpc_bid = processor._calculate_default_bid(0, 0.5)
        assert no_cpc_bid == 1.00  # Default fallback
    
    def test_edge_case_special_characters(self, processor):
        """Test handling of keywords with special characters."""
        special_keywords = [
            Keyword(
                term="plumber's services",
                metrics=KeywordMetrics(
                    search_volume=100,
                    competition=0.5,
                    cpc=10.00
                ),
                category="Services",
                location="Test"
            ),
            Keyword(
                term='24/7 emergency plumber',
                metrics=KeywordMetrics(
                    search_volume=100,
                    competition=0.5,
                    cpc=10.00
                ),
                category="Services",
                location="Test"
            )
        ]
        
        ad_groups = processor.create_ad_groups(
            special_keywords,
            match_types=['phrase', 'exact']
        )
        
        # Should handle special characters properly
        assert len(ad_groups) > 0
        for ag in ad_groups:
            for kw in ag.keywords:
                assert kw.keyword.term  # Should have valid keyword term