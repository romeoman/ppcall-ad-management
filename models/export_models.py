"""Simplified models for data export compatibility."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SimpleAdGroup(BaseModel):
    """
    Simplified Ad Group model for CSV export compatibility.
    
    This model is used for backward compatibility with existing export
    functionality that expects a simpler structure than the full AdGroup model.
    """
    name: str = Field(..., description="Ad group name")
    keywords: List[str] = Field(default_factory=list, description="List of keyword strings")
    match_type: str = Field(default="broad", description="Match type for all keywords")
    campaign_name: Optional[str] = Field(None, description="Campaign name")
    max_cpc: Optional[float] = Field(None, description="Max CPC bid")
    
    @classmethod
    def from_full_ad_group(cls, ad_group, match_type: str = "broad"):
        """
        Create a SimpleAdGroup from a full AdGroup model.
        
        Args:
            ad_group: Full AdGroup model instance
            match_type: Match type to use for export
            
        Returns:
            SimpleAdGroup instance
        """
        # Extract keyword strings from AdGroupKeyword objects
        keyword_strings = []
        if hasattr(ad_group, 'keywords'):
            for kw in ad_group.keywords:
                if hasattr(kw, 'keyword') and hasattr(kw.keyword, 'term'):
                    keyword_strings.append(kw.keyword.term)
                elif isinstance(kw, str):
                    keyword_strings.append(kw)
        
        return cls(
            name=ad_group.name,
            keywords=keyword_strings,
            match_type=match_type,
            campaign_name=ad_group.campaign_name if hasattr(ad_group, 'campaign_name') else None,
            max_cpc=ad_group.default_bid if hasattr(ad_group, 'default_bid') else None
        )
    
    def to_full_ad_group(self):
        """
        Convert to a full AdGroup model.
        
        This is a placeholder for future conversion if needed.
        """
        # This would need proper imports and conversion logic
        raise NotImplementedError("Conversion to full AdGroup not yet implemented")