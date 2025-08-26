"""Unit tests for ad group models."""

import pytest
from models.ad_group_models import (
    AdGroup,
    AdGroupKeyword,
    AdGroupLocation,
    AdGroupConfig,
    AdGroupStatus
)
from models.keyword_models import Keyword, MatchType


class TestAdGroupKeyword:
    """Test AdGroupKeyword model."""
    
    def test_basic_ad_group_keyword(self):
        """Test creating an ad group keyword."""
        keyword = Keyword(term="plumber near me")
        ad_keyword = AdGroupKeyword(
            keyword=keyword,
            bid=2.50,
            final_url="https://example.com/plumber"
        )
        assert ad_keyword.keyword.term == "plumber near me"
        assert ad_keyword.bid == 2.50
        assert ad_keyword.final_url == "https://example.com/plumber"
    
    def test_bid_rounding(self):
        """Test bid is rounded to 2 decimal places."""
        keyword = Keyword(term="test")
        ad_keyword = AdGroupKeyword(keyword=keyword, bid=2.567)
        assert ad_keyword.bid == 2.57
    
    def test_custom_parameters(self):
        """Test custom parameters for tracking."""
        keyword = Keyword(term="test")
        ad_keyword = AdGroupKeyword(
            keyword=keyword,
            custom_parameters={"source": "google", "campaign": "test"}
        )
        assert ad_keyword.custom_parameters["source"] == "google"
        assert ad_keyword.custom_parameters["campaign"] == "test"


class TestAdGroupLocation:
    """Test AdGroupLocation model."""
    
    def test_basic_location(self):
        """Test creating a location target."""
        location = AdGroupLocation(
            name="New York",
            type="city",
            target_id="1023191",
            bid_modifier=1.2
        )
        assert location.name == "New York"
        assert location.type == "city"
        assert location.target_id == "1023191"
        assert location.bid_modifier == 1.2
    
    def test_radius_location(self):
        """Test radius-based location."""
        location = AdGroupLocation(
            name="10 miles around ZIP 10001",
            type="radius",
            radius=10
        )
        assert location.type == "radius"
        assert location.radius == 10
    
    def test_bid_modifier_bounds(self):
        """Test bid modifier bounds."""
        with pytest.raises(ValueError):
            AdGroupLocation(name="Test", type="city", bid_modifier=0.05)  # Below 0.1
        
        with pytest.raises(ValueError):
            AdGroupLocation(name="Test", type="city", bid_modifier=11.0)  # Above 10.0
    
    def test_location_types(self):
        """Test valid location types."""
        valid_types = ["city", "state", "country", "zip", "radius"]
        for loc_type in valid_types:
            location = AdGroupLocation(name="Test", type=loc_type)
            assert location.type == loc_type
        
        with pytest.raises(ValueError):
            AdGroupLocation(name="Test", type="invalid")


class TestAdGroup:
    """Test AdGroup model."""
    
    def test_basic_ad_group(self):
        """Test creating an ad group."""
        ad_group = AdGroup(
            name="Plumbing Services - New York",
            campaign_name="Plumber Campaign",
            default_bid=2.00
        )
        assert ad_group.name == "Plumbing Services - New York"
        assert ad_group.campaign_name == "Plumber Campaign"
        assert ad_group.default_bid == 2.00
        assert ad_group.status == AdGroupStatus.DRAFT
    
    def test_name_cleaning(self):
        """Test ad group name cleaning."""
        ad_group = AdGroup(
            name="Test <Group> \"Name\"",
            campaign_name="Test",
            default_bid=1.0
        )
        assert "<" not in ad_group.name
        assert ">" not in ad_group.name
        assert '"' not in ad_group.name
    
    def test_with_keywords(self):
        """Test ad group with keywords."""
        keyword1 = Keyword(term="plumber", match_type=MatchType.EXACT)
        keyword2 = Keyword(term="plumber near me", match_type=MatchType.PHRASE)
        
        ad_group = AdGroup(
            name="Test Group",
            campaign_name="Test Campaign",
            keywords=[
                AdGroupKeyword(keyword=keyword1, bid=2.0),
                AdGroupKeyword(keyword=keyword2, bid=2.5)
            ],
            default_bid=1.50
        )
        
        assert len(ad_group.keywords) == 2
        assert ad_group.get_total_keywords() == 2
        
        keyword_counts = ad_group.get_keyword_count()
        assert keyword_counts[MatchType.EXACT] == 1
        assert keyword_counts[MatchType.PHRASE] == 1
    
    def test_with_locations(self):
        """Test ad group with location targeting."""
        location1 = AdGroupLocation(name="New York", type="city")
        location2 = AdGroupLocation(name="Los Angeles", type="city")
        
        ad_group = AdGroup(
            name="Test Group",
            campaign_name="Test Campaign",
            locations=[location1, location2],
            default_bid=1.50
        )
        
        assert len(ad_group.locations) == 2
        assert "New York" in ad_group.get_location_names()
        assert "Los Angeles" in ad_group.get_location_names()
    
    def test_negative_keywords(self):
        """Test ad group with negative keywords."""
        ad_group = AdGroup(
            name="Test Group",
            campaign_name="Test Campaign",
            negative_keywords=["free", "cheap", "diy"],
            default_bid=1.50
        )
        assert len(ad_group.negative_keywords) == 3
        assert "free" in ad_group.negative_keywords
    
    def test_to_google_ads_dict(self):
        """Test conversion to Google Ads export format."""
        ad_group = AdGroup(
            name="Test Group",
            campaign_name="Test Campaign",
            default_bid=2.00,
            status=AdGroupStatus.ENABLED
        )
        
        export_dict = ad_group.to_google_ads_dict()
        assert export_dict["Campaign"] == "Test Campaign"
        assert export_dict["Ad Group"] == "Test Group"
        assert export_dict["Status"] == AdGroupStatus.ENABLED
        assert export_dict["Default Max CPC"] == 2.00


class TestAdGroupConfig:
    """Test AdGroupConfig model."""
    
    def test_default_config(self):
        """Test default ad group configuration."""
        config = AdGroupConfig()
        assert config.max_keywords_per_group == 20
        assert config.group_by == "category"
        assert config.include_locations is True
        assert config.auto_negative_keywords is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = AdGroupConfig(
            max_keywords_per_group=50,
            group_by="location",
            location_bid_adjustment=1.5,
            naming_template="{location} | {category}"
        )
        assert config.max_keywords_per_group == 50
        assert config.group_by == "location"
        assert config.location_bid_adjustment == 1.5
        assert config.naming_template == "{location} | {category}"
    
    def test_default_match_types(self):
        """Test default match types configuration."""
        config = AdGroupConfig()
        assert MatchType.PHRASE in config.default_match_types
        assert MatchType.EXACT in config.default_match_types
        assert len(config.default_match_types) == 2
    
    def test_bid_adjustment_rounding(self):
        """Test bid adjustment is rounded."""
        config = AdGroupConfig(location_bid_adjustment=1.567)
        assert config.location_bid_adjustment == 1.57
    
    def test_config_bounds(self):
        """Test configuration value bounds."""
        with pytest.raises(ValueError):
            AdGroupConfig(max_keywords_per_group=0)  # Below 1
        
        with pytest.raises(ValueError):
            AdGroupConfig(max_keywords_per_group=101)  # Above 100
        
        with pytest.raises(ValueError):
            AdGroupConfig(negative_keyword_threshold=1.5)  # Above 1.0