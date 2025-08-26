"""Competition analysis data models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl
from datetime import datetime
from .keyword_models import Keyword, KeywordMetrics


class CompetitorDomain(BaseModel):
    """Competitor domain information."""
    domain: str = Field(..., description="Competitor domain")
    url: Optional[HttpUrl] = None
    organic_keywords: int = Field(default=0, ge=0)
    paid_keywords: int = Field(default=0, ge=0)
    traffic_estimate: Optional[int] = Field(None, ge=0)
    domain_authority: Optional[int] = Field(None, ge=0, le=100)
    last_updated: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('domain')
    def clean_domain(cls, v):
        """Clean and normalize domain."""
        v = v.lower().strip()
        # Remove protocol if present
        v = v.replace('https://', '').replace('http://', '')
        # Remove trailing slash
        v = v.rstrip('/')
        return v


class CompetitorKeyword(BaseModel):
    """Keyword data from competitor analysis."""
    keyword: Keyword
    competitor_domain: str
    position: Optional[int] = Field(None, ge=1, le=100)
    is_paid: bool = Field(default=False)
    ad_copy: Optional[str] = None
    landing_page: Optional[str] = None
    estimated_traffic: Optional[int] = Field(None, ge=0)
    bid_estimate: Optional[float] = Field(None, ge=0)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    @field_validator('bid_estimate')
    def validate_bid(cls, v):
        """Round bid estimate to 2 decimal places."""
        return round(v, 2) if v is not None else None
    
    def is_opportunity(self, min_volume: int = 100, max_competition: float = 0.7) -> bool:
        """Check if this keyword represents an opportunity."""
        if not self.keyword.metrics:
            return False
        
        volume_ok = (self.keyword.metrics.search_volume or 0) >= min_volume
        competition_ok = (self.keyword.metrics.competition or 1.0) <= max_competition
        
        return volume_ok and competition_ok


class KeywordGap(BaseModel):
    """Keyword gap analysis between domains."""
    keyword: Keyword
    our_domain: str
    competitor_domains: List[str]
    gap_type: str = Field(..., pattern="^(missing|underperforming|opportunity)$")
    our_position: Optional[int] = Field(None, ge=1, le=100)
    best_competitor_position: Optional[int] = Field(None, ge=1, le=100)
    recommendation: str
    priority: int = Field(default=1, ge=1, le=5)
    potential_traffic: Optional[int] = Field(None, ge=0)
    
    def calculate_opportunity_score(self) -> float:
        """Calculate opportunity score for this gap."""
        score = 0.0
        
        # Higher score for completely missing keywords
        if self.gap_type == "missing":
            score += 0.5
        elif self.gap_type == "underperforming":
            score += 0.3
        else:
            score += 0.1
        
        # Factor in potential traffic
        if self.potential_traffic:
            if self.potential_traffic > 1000:
                score += 0.3
            elif self.potential_traffic > 100:
                score += 0.2
            else:
                score += 0.1
        
        # Factor in competitor performance
        if self.best_competitor_position:
            if self.best_competitor_position <= 3:
                score += 0.2
            elif self.best_competitor_position <= 10:
                score += 0.1
        
        return min(score, 1.0)


class SpyFuData(BaseModel):
    """SpyFu CSV data structure."""
    domain: str
    keyword: str
    rank: Optional[int] = Field(None, ge=1)
    local_monthly_searches: Optional[int] = Field(None, ge=0)
    global_monthly_searches: Optional[int] = Field(None, ge=0)
    cpc: Optional[float] = Field(None, ge=0)
    difficulty: Optional[float] = Field(None, ge=0, le=100)
    clicks_per_search: Optional[float] = Field(None, ge=0, le=1)
    ad_position: Optional[int] = Field(None, ge=1, le=10)
    ad_clicks_per_month: Optional[int] = Field(None, ge=0)
    ad_cost_per_month: Optional[float] = Field(None, ge=0)
    
    @field_validator('cpc', 'ad_cost_per_month')
    def round_money(cls, v):
        """Round monetary values to 2 decimal places."""
        return round(v, 2) if v is not None else None
    
    def to_keyword(self) -> Keyword:
        """Convert SpyFu data to standard Keyword model."""
        metrics = KeywordMetrics(
            search_volume=self.local_monthly_searches,
            cpc=self.cpc,
            competition=self.difficulty / 100 if self.difficulty else None,
        )
        
        return Keyword(
            term=self.keyword,
            metrics=metrics,
            source="spyfu",
            metadata={
                "domain": self.domain,
                "rank": self.rank,
                "global_searches": self.global_monthly_searches,
                "clicks_per_search": self.clicks_per_search,
            }
        )


class CompetitorAnalysis(BaseModel):
    """Complete competitor analysis results."""
    analysis_date: datetime = Field(default_factory=datetime.now)
    our_domain: str
    competitors: List[CompetitorDomain]
    competitor_keywords: List[CompetitorKeyword]
    keyword_gaps: List[KeywordGap]
    overlap_keywords: List[Keyword]
    unique_keywords: List[Keyword]
    recommendations: List[str] = Field(default_factory=list)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)
    
    def get_top_opportunities(self, limit: int = 10) -> List[KeywordGap]:
        """Get top keyword opportunities sorted by score."""
        sorted_gaps = sorted(
            self.keyword_gaps,
            key=lambda x: x.calculate_opportunity_score(),
            reverse=True
        )
        return sorted_gaps[:limit]
    
    def get_competitor_summary(self) -> Dict[str, Any]:
        """Get summary statistics for competitor analysis."""
        return {
            "total_competitors": len(self.competitors),
            "total_competitor_keywords": len(self.competitor_keywords),
            "total_gaps": len(self.keyword_gaps),
            "total_overlap": len(self.overlap_keywords),
            "total_unique": len(self.unique_keywords),
            "missing_keywords": len([g for g in self.keyword_gaps if g.gap_type == "missing"]),
            "underperforming_keywords": len([g for g in self.keyword_gaps if g.gap_type == "underperforming"]),
            "opportunity_keywords": len([g for g in self.keyword_gaps if g.gap_type == "opportunity"]),
        }
    
