"""Google Ads API client for DataForSEO - PPC focused implementation."""

from typing import Dict, Any, Optional, List
from .base_dataforseo import BaseDataForSEOClient


class GoogleAdsClient(BaseDataForSEOClient):
    """
    Google Ads specific client for DataForSEO API.
    Implements all 6 Google Ads endpoints for PPC campaigns.
    
    Documentation: https://dataforseo.com/apis/google-ads-api
    """
    
    async def get_search_volume(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        include_adult_keywords: bool = False,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get search volume data for Google Ads keywords (up to 1000 keywords).
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/
        
        Args:
            keywords: List of keywords (up to 1000)
            location_code: Target location code (e.g., 2840 for USA)
            language_code: Target language code (e.g., "en")
            date_from: Start date for historical data (YYYY-MM-DD)
            date_to: End date for historical data (YYYY-MM-DD)
            include_adult_keywords: Include adult/sensitive keywords
            sort_by: Sort results by metric (e.g., "search_volume", "cpc")
            
        Returns:
            Search volume data including:
            - Monthly searches (latest)
            - Competition level (0-1)
            - CPC (cost per click)
            - Monthly search history (12 months)
            - Low/high bid estimates
        """
        endpoint = "keywords_data/google_ads/search_volume/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        # Add optional parameters
        if date_from:
            task["date_from"] = date_from
        if date_to:
            task["date_to"] = date_to
        if include_adult_keywords:
            task["include_adult_keywords"] = include_adult_keywords
        if sort_by:
            task["sort_by"] = sort_by
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keywords_for_site(
        self,
        target: str,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        include_branded_keywords: bool = True,
        include_non_branded_keywords: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Extract keywords relevant to a specific website for competitor analysis.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/
        
        Args:
            target: URL of the website to analyze
            location_code: Target location code
            language_code: Target language code
            include_branded_keywords: Include branded terms
            include_non_branded_keywords: Include non-branded terms
            limit: Number of results to return
            offset: Offset for pagination
            
        Returns:
            Keywords relevant to the website with metrics
        """
        endpoint = "keywords_data/google_ads/keywords_for_site/live"
        
        task = {
            "target": target,
            "location_code": self.format_location_code(location_code),
            "language_code": self.format_language_code(language_code),
            "include_branded_keywords": include_branded_keywords,
            "include_non_branded_keywords": include_non_branded_keywords,
            "limit": limit,
            "offset": offset
        }
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keywords_for_keywords(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        include_seed_keyword: bool = True,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate keyword suggestions and related keywords from seed keywords.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/
        
        Args:
            keywords: Seed keywords for expansion
            location_code: Target location code
            language_code: Target language code
            include_seed_keyword: Include original keywords in results
            limit: Number of suggestions to return
            offset: Offset for pagination
            sort_by: Sort results by metric
            
        Returns:
            Related keywords with search volume, competition, and CPC
        """
        endpoint = "keywords_data/google_ads/keywords_for_keywords/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        task.update({
            "include_seed_keyword": include_seed_keyword,
            "limit": limit,
            "offset": offset
        })
        
        if sort_by:
            task["sort_by"] = sort_by
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_ad_traffic_by_keywords(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        bid: Optional[float] = None,
        match: str = "exact",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Estimate traffic and bid ranges for Google Ads campaigns.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/
        
        Args:
            keywords: Keywords to estimate traffic for
            location_code: Target location code
            language_code: Target language code
            bid: Max CPC bid for estimates
            match: Match type (exact, phrase, broad)
            date_from: Start date for forecasting
            date_to: End date for forecasting
            
        Returns:
            Traffic estimates including:
            - Estimated clicks per day
            - Estimated impressions
            - Average CPC
            - Total cost projections
            - CTR predictions
        """
        endpoint = "keywords_data/google_ads/ad_traffic_by_keywords/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        task["match"] = match
        
        if bid is not None:
            task["bid"] = bid
        if date_from:
            task["date_from"] = date_from
        if date_to:
            task["date_to"] = date_to
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_locations(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get supported Google Ads locations.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/
        
        Args:
            country: Optional country code filter
            
        Returns:
            List of supported locations with codes
        """
        endpoint = "keywords_data/google_ads/locations"
        
        if country:
            endpoint = f"{endpoint}/{country}"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_languages(self) -> List[Dict[str, Any]]:
        """
        Get supported Google Ads languages.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/
        
        Returns:
            List of supported languages with codes
        """
        endpoint = "keywords_data/google_ads/languages"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get Google Ads categories for keyword research.
        
        Returns:
            List of available categories with IDs
        """
        endpoint = "keywords_data/google_ads/categories"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get Google Ads API status and limits.
        
        Returns:
            API status information and rate limits
        """
        endpoint = "keywords_data/google_ads/status"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)