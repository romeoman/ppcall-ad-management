"""Keyword-related data models for the Ad Management system."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime


class MatchType(str, Enum):
    """Keyword match types for Google Ads."""
    BROAD = "broad"
    PHRASE = "phrase"
    EXACT = "exact"
    BROAD_MODIFIER = "broad_modifier"


class KeywordStatus(str, Enum):
    """Keyword processing status."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    EXCLUDED = "excluded"


class KeywordMetrics(BaseModel):
    """Metrics associated with a keyword."""
    search_volume: Optional[int] = Field(None, ge=0, description="Monthly search volume")
    cpc: Optional[float] = Field(None, ge=0, description="Cost per click in USD")
    competition: Optional[float] = Field(None, ge=0, le=1, description="Competition score (0-1)")
    competition_level: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    trend: Optional[List[int]] = Field(None, description="Monthly trend data")
    
    @field_validator('cpc')
    def validate_cpc(cls, v):
        """Ensure CPC is positive if provided."""
        if v is not None and v < 0:
            raise ValueError('CPC must be positive')
        return round(v, 2) if v is not None else None


class Keyword(BaseModel):
    """Core keyword model."""
    term: str = Field(..., min_length=1, max_length=500)
    match_type: MatchType = Field(default=MatchType.BROAD)
    metrics: Optional[KeywordMetrics] = None
    category: Optional[str] = None
    location: Optional[str] = None
    language: str = Field(default="en")
    status: KeywordStatus = Field(default=KeywordStatus.PENDING)
    source: str = Field(default="manual", description="Source of the keyword")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('term')
    def clean_term(cls, v):
        """Clean and normalize keyword term."""
        return v.strip().lower()
    
    def to_google_ads_format(self) -> str:
        """Convert to Google Ads format based on match type."""
        if self.match_type == MatchType.EXACT:
            return f"[{self.term}]"
        elif self.match_type == MatchType.PHRASE:
            return f'"{self.term}"'
        elif self.match_type == MatchType.BROAD_MODIFIER:
            words = self.term.split()
            return " ".join(f"+{word}" for word in words)
        else:  # BROAD
            return self.term
    
    model_config = {"use_enum_values": True}


class NegativeKeyword(BaseModel):
    """Negative keyword model."""
    term: str = Field(..., min_length=1, max_length=500)
    reason: str = Field(..., description="Reason for exclusion")
    match_type: MatchType = Field(default=MatchType.PHRASE)
    scope: str = Field(default="campaign", pattern="^(campaign|ad_group)$")
    auto_generated: bool = Field(default=False)
    confidence: float = Field(default=1.0, ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('term')
    def clean_term(cls, v):
        """Clean and normalize negative keyword term."""
        return v.strip().lower()


class KeywordCategory(BaseModel):
    """Category for grouping keywords."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_category: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    priority: int = Field(default=0, ge=0, le=10)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KeywordExpansion(BaseModel):
    """Expanded keyword from seed keyword."""
    seed_keyword: str = Field(..., description="Original seed keyword")
    expanded_term: str = Field(..., description="Expanded keyword term")
    expansion_type: str = Field(..., pattern="^(related|similar|long_tail|question)$")
    relevance_score: float = Field(..., ge=0, le=1)
    metrics: Optional[KeywordMetrics] = None
    approved: bool = Field(default=False)
    
    @field_validator('relevance_score')
    def validate_relevance(cls, v):
        """Round relevance score to 2 decimal places."""
        return round(v, 2)


class SeedKeyword(BaseModel):
    """Initial seed keyword for expansion."""
    term: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = None
    location: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)
    expansion_limit: int = Field(default=50, ge=1, le=1000)
    include_questions: bool = Field(default=True)
    include_long_tail: bool = Field(default=True)
    min_search_volume: Optional[int] = Field(None, ge=0)
    max_cpc: Optional[float] = Field(None, ge=0)
    
    @field_validator('term')
    def clean_term(cls, v):
        """Clean and normalize seed keyword."""
        return v.strip().lower()