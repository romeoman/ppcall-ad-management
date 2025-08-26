"""Ad group related data models for organizing keywords."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from .keyword_models import Keyword, MatchType


class AdGroupStatus(str):
    """Ad group status options."""
    DRAFT = "draft"
    ENABLED = "enabled"
    PAUSED = "paused"
    REMOVED = "removed"


class AdGroupKeyword(BaseModel):
    """Keyword within an ad group with specific settings."""
    keyword: Keyword
    bid: Optional[float] = Field(None, ge=0, description="Max CPC bid")
    final_url: Optional[str] = None
    tracking_template: Optional[str] = None
    custom_parameters: Dict[str, str] = Field(default_factory=dict)
    
    @field_validator('bid')
    def validate_bid(cls, v):
        """Round bid to 2 decimal places."""
        return round(v, 2) if v is not None else None


class AdGroupLocation(BaseModel):
    """Location targeting for an ad group."""
    name: str = Field(..., description="Location name")
    type: str = Field(..., pattern="^(city|state|country|zip|radius)$")
    target_id: Optional[str] = Field(None, description="Google Ads location ID")
    radius: Optional[int] = Field(None, ge=1, le=500, description="Radius in miles")
    bid_modifier: float = Field(default=1.0, ge=0.1, le=10.0)
    
    @field_validator('bid_modifier')
    def validate_bid_modifier(cls, v):
        """Ensure bid modifier is within Google Ads limits."""
        return round(v, 2)


class AdGroup(BaseModel):
    """Ad group model for organizing keywords."""
    name: str = Field(..., min_length=1, max_length=255)
    campaign_name: str = Field(..., min_length=1, max_length=255)
    keywords: List[AdGroupKeyword] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)
    locations: List[AdGroupLocation] = Field(default_factory=list)
    default_bid: float = Field(..., ge=0.01, description="Default max CPC")
    status: str = Field(default=AdGroupStatus.DRAFT)
    ad_rotation: str = Field(default="OPTIMIZE", pattern="^(OPTIMIZE|ROTATE_INDEFINITELY)$")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    def validate_name(cls, v):
        """Ensure ad group name follows Google Ads conventions."""
        # Remove special characters that might cause issues
        invalid_chars = ['<', '>', '"', "'", '&']
        for char in invalid_chars:
            v = v.replace(char, '')
        return v.strip()
    
    @field_validator('default_bid')
    def validate_default_bid(cls, v):
        """Round default bid to 2 decimal places."""
        return round(v, 2)
    
    def get_keyword_count(self) -> Dict[str, int]:
        """Get count of keywords by match type."""
        counts = {match_type: 0 for match_type in MatchType}
        for ad_keyword in self.keywords:
            counts[ad_keyword.keyword.match_type] += 1
        return counts
    
    def get_total_keywords(self) -> int:
        """Get total number of keywords in the ad group."""
        return len(self.keywords)
    
    def get_location_names(self) -> List[str]:
        """Get list of location names for targeting."""
        return [loc.name for loc in self.locations]
    
    def to_google_ads_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for Google Ads export."""
        return {
            "Campaign": self.campaign_name,
            "Ad Group": self.name,
            "Status": self.status,
            "Default Max CPC": self.default_bid,
            "Ad Rotation": self.ad_rotation,
            "Keyword Count": self.get_total_keywords(),
            "Location Targets": ", ".join(self.get_location_names()),
            "Negative Keywords": len(self.negative_keywords),
        }
    


class AdGroupConfig(BaseModel):
    """Configuration for ad group generation."""
    max_keywords_per_group: int = Field(default=20, ge=1, le=100)
    group_by: str = Field(default="category", pattern="^(category|location|theme|custom)$")
    include_locations: bool = Field(default=True)
    location_bid_adjustment: float = Field(default=1.0, ge=0.1, le=10.0)
    naming_template: str = Field(default="{category} - {location}")
    default_match_types: List[MatchType] = Field(default_factory=lambda: [MatchType.PHRASE, MatchType.EXACT])
    auto_negative_keywords: bool = Field(default=True)
    negative_keyword_threshold: float = Field(default=0.8, ge=0, le=1)
    
    @field_validator('location_bid_adjustment')
    def validate_bid_adjustment(cls, v):
        """Round bid adjustment to 2 decimal places."""
        return round(v, 2)