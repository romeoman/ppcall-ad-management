"""Data models for Ad Management system using Pydantic."""

from .keyword_models import (
    Keyword,
    NegativeKeyword,
    KeywordMetrics,
    KeywordCategory,
    KeywordExpansion,
    SeedKeyword,
)
from .ad_group_models import (
    AdGroup,
    AdGroupKeyword,
    AdGroupLocation,
    AdGroupConfig,
)
from .competition_models import (
    CompetitorAnalysis,
    CompetitorKeyword,
    CompetitorDomain,
    KeywordGap,
    SpyFuData,
)
from .api_models import (
    DataForSEORequest,
    DataForSEOResponse,
    SERPRequest,
    SERPResponse,
    FireCrawlRequest,
    FireCrawlResponse,
    ScrapedContent,
)
from .output_models import (
    ExportConfig,
    CSVExport,
    GoogleAdsExport,
    ProjectExport,
    ConsolidatedOutput,
)
from .project_models import (
    ProjectConfig,
    ProjectInputs,
    ProjectOutputs,
    ProjectMetadata,
)

__all__ = [
    # Keyword models
    "Keyword",
    "NegativeKeyword",
    "KeywordMetrics",
    "KeywordCategory",
    "KeywordExpansion",
    "SeedKeyword",
    # Ad group models
    "AdGroup",
    "AdGroupKeyword",
    "AdGroupLocation",
    "AdGroupConfig",
    # Competition models
    "CompetitorAnalysis",
    "CompetitorKeyword",
    "CompetitorDomain",
    "KeywordGap",
    "SpyFuData",
    # API models
    "DataForSEORequest",
    "DataForSEOResponse",
    "SERPRequest",
    "SERPResponse",
    "FireCrawlRequest",
    "FireCrawlResponse",
    "ScrapedContent",
    # Output models
    "ExportConfig",
    "CSVExport",
    "GoogleAdsExport",
    "ProjectExport",
    "ConsolidatedOutput",
    # Project models
    "ProjectConfig",
    "ProjectInputs",
    "ProjectOutputs",
    "ProjectMetadata",
]