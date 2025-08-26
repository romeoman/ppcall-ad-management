"""API request and response models for external services."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, HttpUrl
from datetime import datetime
from .keyword_models import Keyword, KeywordMetrics


# Data4SEO Models
class Data4SEORequest(BaseModel):
    """Request model for Data4SEO API."""
    keywords: List[str] = Field(..., min_length=1, max_length=1000)
    location_code: int = Field(default=2840, description="Location code (2840 = United States)")
    language_code: str = Field(default="en", pattern="^[a-z]{2}$")
    search_partners: bool = Field(default=False)
    date_from: Optional[str] = Field(None, pattern="^\\d{4}-\\d{2}-\\d{2}$")
    date_to: Optional[str] = Field(None, pattern="^\\d{4}-\\d{2}-\\d{2}$")
    include_seed_keyword_data: bool = Field(default=True)
    include_clickstream_data: bool = Field(default=False)
    include_keyword_difficulty: bool = Field(default=True)
    
    @field_validator('keywords')
    def validate_keywords(cls, v):
        """Clean and validate keywords."""
        return [k.strip().lower() for k in v if k.strip()]
    
    def to_api_payload(self) -> List[Dict[str, Any]]:
        """Convert to Data4SEO API payload format."""
        return [{
            "keywords": self.keywords,
            "location_code": self.location_code,
            "language_code": self.language_code,
            "search_partners": self.search_partners,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }]


class Data4SEOKeywordData(BaseModel):
    """Individual keyword data from Data4SEO response."""
    keyword: str
    location_code: int
    language_code: str
    search_partners: bool
    competition: Optional[float] = Field(None, ge=0, le=1)
    cpc: Optional[float] = Field(None, ge=0)
    search_volume: Optional[int] = Field(None, ge=0)
    monthly_searches: Optional[List[Dict[str, int]]] = None
    keyword_difficulty: Optional[int] = Field(None, ge=0, le=100)
    
    def to_keyword_model(self) -> Keyword:
        """Convert to standard Keyword model."""
        metrics = KeywordMetrics(
            search_volume=self.search_volume,
            cpc=self.cpc,
            competition=self.competition,
            competition_level="high" if (self.competition or 0) > 0.7 else "medium" if (self.competition or 0) > 0.3 else "low"
        )
        
        return Keyword(
            term=self.keyword,
            metrics=metrics,
            source="data4seo",
            metadata={
                "location_code": self.location_code,
                "keyword_difficulty": self.keyword_difficulty,
            }
        )


class Data4SEOResponse(BaseModel):
    """Response model from Data4SEO API."""
    version: str
    status_code: int
    status_message: str
    time: str
    cost: float
    tasks_count: int
    tasks_error: int
    tasks: List[Dict[str, Any]]
    
    def get_keyword_data(self) -> List[Data4SEOKeywordData]:
        """Extract keyword data from response."""
        keywords = []
        for task in self.tasks:
            if task.get("status_code") == 20000 and "result" in task:
                for result in task["result"]:
                    if "items" in result:
                        for item in result["items"]:
                            keywords.append(Data4SEOKeywordData(**item))
        return keywords


# SERP API Models
class SERPRequest(BaseModel):
    """Request model for SERP API."""
    keyword: str = Field(..., min_length=1)
    location: str = Field(default="United States")
    device: str = Field(default="desktop", pattern="^(desktop|mobile|tablet)$")
    engine: str = Field(default="google", pattern="^(google|bing|yahoo|baidu|yandex)$")
    num_results: int = Field(default=100, ge=10, le=100)
    include_ads: bool = Field(default=True)
    include_organic: bool = Field(default=True)
    
    def to_api_params(self) -> Dict[str, Any]:
        """Convert to SERP API parameters."""
        return {
            "q": self.keyword,
            "location": self.location,
            "device": self.device,
            "engine": self.engine,
            "num": self.num_results,
        }


class SERPResult(BaseModel):
    """Individual SERP result."""
    position: int = Field(..., ge=1)
    title: str
    link: HttpUrl
    snippet: Optional[str] = None
    displayed_link: Optional[str] = None
    is_ad: bool = Field(default=False)
    ad_position: Optional[int] = None
    site_links: List[Dict[str, str]] = Field(default_factory=list)


class SERPResponse(BaseModel):
    """Response model from SERP API."""
    keyword: str
    total_results: int
    search_time: float
    organic_results: List[SERPResult] = Field(default_factory=list)
    paid_results: List[SERPResult] = Field(default_factory=list)
    related_searches: List[str] = Field(default_factory=list)
    people_also_ask: List[Dict[str, str]] = Field(default_factory=list)
    
    def get_competitors(self, limit: int = 10) -> List[str]:
        """Extract competitor domains from results."""
        domains = set()
        for result in self.organic_results[:limit]:
            domain = str(result.link).split('/')[2]
            domains.add(domain)
        for result in self.paid_results[:limit]:
            domain = str(result.link).split('/')[2]
            domains.add(domain)
        return list(domains)


# FireCrawl Models
class FireCrawlRequest(BaseModel):
    """Request model for FireCrawl API."""
    url: HttpUrl
    formats: List[str] = Field(default=["markdown", "html"], description="Output formats")
    only_main_content: bool = Field(default=True)
    include_tags: List[str] = Field(default_factory=list)
    exclude_tags: List[str] = Field(default_factory=list)
    wait_for: int = Field(default=0, ge=0, le=10000, description="Wait time in ms")
    timeout: int = Field(default=30000, ge=1000, le=60000)
    
    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to FireCrawl API payload."""
        return {
            "url": str(self.url),
            "formats": self.formats,
            "onlyMainContent": self.only_main_content,
            "includeTags": self.include_tags,
            "excludeTags": self.exclude_tags,
            "waitFor": self.wait_for,
            "timeout": self.timeout,
        }


class ScrapedContent(BaseModel):
    """Scraped content from a webpage."""
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    h1: Optional[str] = None
    headings: List[str] = Field(default_factory=list)
    body_text: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    meta_tags: Dict[str, str] = Field(default_factory=dict)
    cta_texts: List[str] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    def extract_keywords(self, min_length: int = 3) -> List[str]:
        """Extract potential keywords from content."""
        text = (self.body_text or "") + " " + (self.title or "")
        words = text.lower().split()
        
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if len(word) >= min_length:
                keywords.append(word)
        
        # Return unique keywords
        return list(set(keywords))
    
    def get_cta_elements(self) -> List[str]:
        """Extract CTA elements from scraped content."""
        cta_keywords = [
            "buy now", "get started", "sign up", "learn more",
            "contact us", "download", "try free", "book now",
            "request quote", "schedule", "call now"
        ]
        
        ctas = []
        text = (self.body_text or "").lower()
        
        for keyword in cta_keywords:
            if keyword in text:
                ctas.append(keyword)
        
        return ctas


class FireCrawlResponse(BaseModel):
    """Response model from FireCrawl API."""
    success: bool
    data: Optional[ScrapedContent] = None
    error: Optional[str] = None
    credits_used: Optional[int] = None
    credits_remaining: Optional[int] = None
    
    def is_successful(self) -> bool:
        """Check if scraping was successful."""
        return self.success and self.data is not None