"""API Integration package for DataForSEO, SERP, and FireCrawl APIs."""

from .base_client import BaseAPIClient
from .dataforseo_client import DataForSEOClient  # Legacy, will be deprecated
from .dataforseo.google_ads_client import GoogleAdsClient
from .dataforseo.bing_ads_client import BingAdsClient
from .serper_client import SerperClient
from .firecrawl_client import FireCrawlClient

__all__ = [
    'BaseAPIClient',
    'DataForSEOClient',  # Legacy, will be deprecated
    'GoogleAdsClient',
    'BingAdsClient',
    'SerperClient',
    'FireCrawlClient',
]