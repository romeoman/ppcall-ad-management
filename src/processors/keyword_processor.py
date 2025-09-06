"""
Keyword Processor Module

Handles keyword expansion, categorization, and enrichment using DataForSEO APIs.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict

from api_integration.dataforseo.google_ads_client import GoogleAdsClient
from api_integration.dataforseo.bing_ads_client import BingAdsClient
from models.keyword_models import Keyword, KeywordMetrics, ExpandedKeyword
from models.location_models import Location

# Configure logging
logger = logging.getLogger(__name__)


class KeywordProcessor:
    """
    Processes keywords including expansion, categorization, and enrichment.
    """
    
    def __init__(
        self,
        google_ads_client: Optional[GoogleAdsClient] = None,
        bing_ads_client: Optional[BingAdsClient] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24
    ):
        """
        Initialize KeywordProcessor with API clients and caching.
        
        Args:
            google_ads_client: Google Ads API client
            bing_ads_client: Bing Ads API client
            cache_dir: Directory for caching API responses
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.google_ads_client = google_ads_client
        self.bing_ads_client = bing_ads_client
        self.cache_dir = cache_dir
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("KeywordProcessor initialized")
    
    def expand_seed_keywords(
        self,
        seed_keywords: List[Dict[str, Any]],
        platform: str = "google_ads",
        location_code: int = 2840,  # Default: USA
        language_code: str = "en",
        include_seed_in_results: bool = True
    ) -> List[ExpandedKeyword]:
        """
        Expand seed keywords using API data.
        
        Args:
            seed_keywords: List of seed keyword dictionaries with 'keyword' and 'category'
            platform: Target platform ('google_ads' or 'bing_ads')
            location_code: Location code for targeting
            language_code: Language code for targeting
            include_seed_in_results: Whether to include seed keywords in results
        
        Returns:
            List of expanded keywords with metrics
        """
        expanded_keywords = []
        processed_terms = set()
        
        for seed in seed_keywords:
            seed_term = seed.get('keyword', seed.get('Keyword', ''))
            category = seed.get('category', seed.get('Category', 'general'))
            
            if not seed_term:
                logger.warning(f"Empty seed keyword found, skipping")
                continue
            
            try:
                logger.info(f"Expanding seed keyword: '{seed_term}' (category: {category})")
                
                # Check cache first
                cached_result = self._get_cached_expansion(seed_term, platform, location_code)
                if cached_result:
                    logger.info(f"Using cached expansion for '{seed_term}'")
                    suggestions = cached_result
                else:
                    # Get suggestions from appropriate API
                    if platform == "google_ads" and self.google_ads_client:
                        suggestions = self._expand_with_google_ads(
                            seed_term, location_code, language_code
                        )
                    elif platform == "bing_ads" and self.bing_ads_client:
                        suggestions = self._expand_with_bing_ads(
                            seed_term, location_code, language_code
                        )
                    else:
                        logger.warning(f"No client available for platform: {platform}")
                        suggestions = []
                    
                    # Cache the result
                    if suggestions:
                        self._cache_expansion(seed_term, platform, location_code, suggestions)
                
                # Process suggestions
                for suggestion in suggestions:
                    keyword_term = suggestion.get('keyword', '')
                    
                    # Skip duplicates
                    if keyword_term in processed_terms:
                        continue
                    
                    processed_terms.add(keyword_term)
                    
                    # Create expanded keyword
                    expanded_keyword = ExpandedKeyword(
                        keyword=keyword_term,
                        seed_keyword=seed_term,
                        category=category,
                        search_volume=suggestion.get('search_volume', 0),
                        competition=suggestion.get('competition', 0),
                        cpc=suggestion.get('cpc', 0),
                        platform=platform,
                        location_code=location_code,
                        language_code=language_code
                    )
                    
                    expanded_keywords.append(expanded_keyword)
                
                # Include seed keyword if requested
                if include_seed_in_results and seed_term not in processed_terms:
                    seed_expanded = ExpandedKeyword(
                        keyword=seed_term,
                        seed_keyword=seed_term,
                        category=category,
                        search_volume=0,  # Will be enriched later
                        competition=0,
                        cpc=0,
                        platform=platform,
                        location_code=location_code,
                        language_code=language_code
                    )
                    expanded_keywords.append(seed_expanded)
                    processed_terms.add(seed_term)
                
            except Exception as e:
                logger.error(f"Error expanding keyword '{seed_term}': {e}")
        
        logger.info(f"Expanded {len(seed_keywords)} seeds into {len(expanded_keywords)} keywords")
        return expanded_keywords
    
    def _expand_with_google_ads(
        self,
        seed_term: str,
        location_code: int,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Expand keywords using Google Ads API."""
        try:
            # Use Keywords for Keywords endpoint
            response = self.google_ads_client.get_keywords_for_keywords(
                keywords=[seed_term],
                location_code=location_code,
                language_code=language_code
            )
            
            suggestions = []
            if response and response.get('tasks'):
                for task in response['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword_data = {
                                'keyword': item.get('keyword', ''),
                                'search_volume': item.get('search_volume', 0),
                                'competition': item.get('competition', 0),
                                'cpc': item.get('cpc', 0)
                            }
                            suggestions.append(keyword_data)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Google Ads expansion error: {e}")
            return []
    
    def _expand_with_bing_ads(
        self,
        seed_term: str,
        location_code: int,
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Expand keywords using Bing Ads API."""
        try:
            # Use Keywords for Keywords endpoint
            response = self.bing_ads_client.get_keywords_for_keywords(
                keywords=[seed_term],
                location_code=location_code,
                language_code=language_code
            )
            
            suggestions = []
            if response and response.get('tasks'):
                for task in response['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword_data = {
                                'keyword': item.get('keyword', ''),
                                'search_volume': item.get('search_volume', 0),
                                'competition': item.get('competition', 0),
                                'cpc': item.get('bid', 0)  # Bing uses 'bid' instead of 'cpc'
                            }
                            suggestions.append(keyword_data)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Bing Ads expansion error: {e}")
            return []
    
    def combine_with_locations(
        self,
        keywords: List[ExpandedKeyword],
        locations: List[Location],
        combination_patterns: Optional[Dict[str, str]] = None
    ) -> List[ExpandedKeyword]:
        """
        Combine keywords with locations to create location-specific keywords.
        
        Args:
            keywords: List of expanded keywords
            locations: List of location objects
            combination_patterns: Optional patterns for combination (e.g., {city}: "{keyword} in {city}")
        
        Returns:
            List of location-combined keywords
        """
        if not combination_patterns:
            combination_patterns = {
                'city': "{keyword} in {city}",
                'city_state': "{keyword} {city} {state}",
                'near': "{keyword} near me",
                'zip': "{keyword} {zip}",
                'near_zip': "{keyword} near {zip}"
            }
        
        combined_keywords = []
        
        for keyword in keywords:
            for location in locations:
                # City combinations
                if location.city:
                    # Pattern: "keyword in city"
                    if 'city' in combination_patterns:
                        combined_term = combination_patterns['city'].format(
                            keyword=keyword.keyword,
                            city=location.city
                        )
                        combined_keyword = ExpandedKeyword(
                            keyword=combined_term,
                            seed_keyword=keyword.seed_keyword,
                            category=keyword.category,
                            search_volume=0,  # Will be enriched
                            competition=keyword.competition,
                            cpc=keyword.cpc,
                            platform=keyword.platform,
                            location_code=keyword.location_code,
                            language_code=keyword.language_code,
                            location_type='city',
                            location_value=location.city
                        )
                        combined_keywords.append(combined_keyword)
                    
                    # Pattern: "keyword city state"
                    if 'city_state' in combination_patterns and location.state:
                        combined_term = combination_patterns['city_state'].format(
                            keyword=keyword.keyword,
                            city=location.city,
                            state=location.state
                        )
                        combined_keyword = ExpandedKeyword(
                            keyword=combined_term,
                            seed_keyword=keyword.seed_keyword,
                            category=keyword.category,
                            search_volume=0,
                            competition=keyword.competition,
                            cpc=keyword.cpc,
                            platform=keyword.platform,
                            location_code=keyword.location_code,
                            language_code=keyword.language_code,
                            location_type='city_state',
                            location_value=f"{location.city}, {location.state}"
                        )
                        combined_keywords.append(combined_keyword)
                
                # Zip code combinations
                if location.zip_code:
                    # Pattern: "keyword zip"
                    if 'zip' in combination_patterns:
                        combined_term = combination_patterns['zip'].format(
                            keyword=keyword.keyword,
                            zip=location.zip_code
                        )
                        combined_keyword = ExpandedKeyword(
                            keyword=combined_term,
                            seed_keyword=keyword.seed_keyword,
                            category=keyword.category,
                            search_volume=0,
                            competition=keyword.competition,
                            cpc=keyword.cpc,
                            platform=keyword.platform,
                            location_code=keyword.location_code,
                            language_code=keyword.language_code,
                            location_type='zip',
                            location_value=location.zip_code
                        )
                        combined_keywords.append(combined_keyword)
                    
                    # Pattern: "keyword near zip"
                    if 'near_zip' in combination_patterns:
                        combined_term = combination_patterns['near_zip'].format(
                            keyword=keyword.keyword,
                            zip=location.zip_code
                        )
                        combined_keyword = ExpandedKeyword(
                            keyword=combined_term,
                            seed_keyword=keyword.seed_keyword,
                            category=keyword.category,
                            search_volume=0,
                            competition=keyword.competition,
                            cpc=keyword.cpc,
                            platform=keyword.platform,
                            location_code=keyword.location_code,
                            language_code=keyword.language_code,
                            location_type='near_zip',
                            location_value=location.zip_code
                        )
                        combined_keywords.append(combined_keyword)
        
        # Add "near me" variants for non-location keywords
        for keyword in keywords:
            if not hasattr(keyword, 'location_type') or not keyword.location_type:
                if 'near' in combination_patterns:
                    combined_term = combination_patterns['near'].format(
                        keyword=keyword.keyword
                    )
                    combined_keyword = ExpandedKeyword(
                        keyword=combined_term,
                        seed_keyword=keyword.seed_keyword,
                        category=keyword.category,
                        search_volume=0,
                        competition=keyword.competition,
                        cpc=keyword.cpc,
                        platform=keyword.platform,
                        location_code=keyword.location_code,
                        language_code=keyword.language_code,
                        location_type='near_me',
                        location_value='near_me'
                    )
                    combined_keywords.append(combined_keyword)
        
        logger.info(f"Combined {len(keywords)} keywords with {len(locations)} locations: "
                   f"{len(combined_keywords)} combinations created")
        
        return combined_keywords
    
    def enrich_keywords_with_metrics(
        self,
        keywords: List[ExpandedKeyword],
        platform: str = "google_ads",
        batch_size: int = 100
    ) -> List[ExpandedKeyword]:
        """
        Enrich keywords with search volume, CPC, and competition data.
        
        Args:
            keywords: List of keywords to enrich
            platform: Target platform for metrics
            batch_size: Number of keywords per API batch
        
        Returns:
            List of enriched keywords
        """
        enriched_keywords = []
        
        # Group keywords into batches
        keyword_batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        
        for batch_num, batch in enumerate(keyword_batches, 1):
            logger.info(f"Enriching batch {batch_num}/{len(keyword_batches)} ({len(batch)} keywords)")
            
            # Extract keyword terms
            keyword_terms = [k.keyword for k in batch]
            
            try:
                # Check cache for metrics
                cached_metrics = self._get_cached_metrics(keyword_terms, platform)
                
                # Identify keywords needing API call
                keywords_to_fetch = []
                for term in keyword_terms:
                    if term not in cached_metrics:
                        keywords_to_fetch.append(term)
                
                # Fetch metrics for uncached keywords
                if keywords_to_fetch:
                    if platform == "google_ads" and self.google_ads_client:
                        metrics = self._get_google_ads_metrics(keywords_to_fetch)
                    elif platform == "bing_ads" and self.bing_ads_client:
                        metrics = self._get_bing_ads_metrics(keywords_to_fetch)
                    else:
                        logger.warning(f"No client available for platform: {platform}")
                        metrics = {}
                    
                    # Cache the fetched metrics
                    for term, metric_data in metrics.items():
                        self._cache_metrics(term, platform, metric_data)
                        cached_metrics[term] = metric_data
                
                # Apply metrics to keywords
                for keyword in batch:
                    if keyword.keyword in cached_metrics:
                        metric_data = cached_metrics[keyword.keyword]
                        keyword.search_volume = metric_data.get('search_volume', 0)
                        keyword.competition = metric_data.get('competition', 0)
                        keyword.cpc = metric_data.get('cpc', 0)
                    
                    enriched_keywords.append(keyword)
                
            except Exception as e:
                logger.error(f"Error enriching batch {batch_num}: {e}")
                # Add keywords without metrics
                enriched_keywords.extend(batch)
        
        logger.info(f"Enriched {len(enriched_keywords)} keywords with metrics")
        return enriched_keywords
    
    def _get_google_ads_metrics(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get metrics from Google Ads API."""
        try:
            response = self.google_ads_client.get_search_volume(
                keywords=keywords
            )
            
            metrics = {}
            if response and response.get('tasks'):
                for task in response['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword = item.get('keyword', '')
                            metrics[keyword] = {
                                'search_volume': item.get('search_volume', 0),
                                'competition': item.get('competition', 0),
                                'cpc': item.get('cpc', 0)
                            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Google Ads metrics error: {e}")
            return {}
    
    def _get_bing_ads_metrics(self, keywords: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get metrics from Bing Ads API."""
        try:
            response = self.bing_ads_client.get_search_volume(
                keywords=keywords
            )
            
            metrics = {}
            if response and response.get('tasks'):
                for task in response['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword = item.get('keyword', '')
                            metrics[keyword] = {
                                'search_volume': item.get('search_volume', 0),
                                'competition': item.get('competition', 0),
                                'cpc': item.get('cpc', 0)
                            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Bing Ads metrics error: {e}")
            return {}
    
    def categorize_keywords(
        self,
        keywords: List[ExpandedKeyword],
        categories: Optional[Dict[str, List[str]]] = None,
        auto_categorize: bool = True
    ) -> List[ExpandedKeyword]:
        """
        Categorize keywords based on rules or patterns.
        
        Args:
            keywords: List of keywords to categorize
            categories: Optional dictionary of category rules
            auto_categorize: Whether to use automatic categorization
        
        Returns:
            List of categorized keywords
        """
        if not categories:
            categories = self._get_default_categories()
        
        for keyword in keywords:
            # Skip if already categorized
            if keyword.category and keyword.category != 'general':
                continue
            
            keyword_lower = keyword.keyword.lower()
            
            # Apply category rules
            for category_name, patterns in categories.items():
                for pattern in patterns:
                    if pattern.lower() in keyword_lower:
                        keyword.category = category_name
                        break
                
                if keyword.category != 'general':
                    break
            
            # Auto-categorize if enabled and no match found
            if auto_categorize and keyword.category == 'general':
                keyword.category = self._auto_categorize(keyword.keyword)
        
        logger.info(f"Categorized {len(keywords)} keywords")
        return keywords
    
    def _get_default_categories(self) -> Dict[str, List[str]]:
        """Get default category patterns."""
        return {
            'emergency': ['emergency', '24/7', 'urgent', 'immediate', 'same day'],
            'repair': ['repair', 'fix', 'broken', 'leak', 'damage'],
            'installation': ['install', 'installation', 'new', 'replacement'],
            'maintenance': ['maintenance', 'service', 'inspection', 'tune-up'],
            'commercial': ['commercial', 'business', 'office', 'industrial'],
            'residential': ['residential', 'home', 'house', 'apartment']
        }
    
    def _auto_categorize(self, keyword: str) -> str:
        """Automatically categorize based on keyword structure."""
        # Simple heuristic categorization
        keyword_lower = keyword.lower()
        
        if any(term in keyword_lower for term in ['near', 'location', 'zip']):
            return 'local'
        elif any(term in keyword_lower for term in ['how', 'what', 'why', 'when']):
            return 'informational'
        elif any(term in keyword_lower for term in ['buy', 'price', 'cost', 'cheap']):
            return 'transactional'
        else:
            return 'general'
    
    def filter_keywords(
        self,
        keywords: List[ExpandedKeyword],
        min_search_volume: int = 10,
        max_cpc: float = 100.0,
        max_competition: float = 1.0,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[ExpandedKeyword]:
        """
        Filter keywords based on metrics and patterns.
        
        Args:
            keywords: List of keywords to filter
            min_search_volume: Minimum search volume threshold
            max_cpc: Maximum CPC threshold
            max_competition: Maximum competition threshold
            exclude_patterns: Patterns to exclude
        
        Returns:
            Filtered list of keywords
        """
        filtered = []
        
        for keyword in keywords:
            # Apply metric filters
            if keyword.search_volume < min_search_volume:
                continue
            if keyword.cpc > max_cpc:
                continue
            if keyword.competition > max_competition:
                continue
            
            # Apply pattern exclusions
            if exclude_patterns:
                exclude = False
                keyword_lower = keyword.keyword.lower()
                for pattern in exclude_patterns:
                    if pattern.lower() in keyword_lower:
                        exclude = True
                        break
                if exclude:
                    continue
            
            filtered.append(keyword)
        
        logger.info(f"Filtered {len(keywords)} keywords to {len(filtered)} "
                   f"(removed {len(keywords) - len(filtered)})")
        
        return filtered
    
    # Caching methods
    
    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        key_str = json.dumps(args, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_expansion(
        self,
        seed_term: str,
        platform: str,
        location_code: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached expansion results."""
        if not self.cache_dir:
            return None
        
        cache_key = self._get_cache_key('expansion', seed_term, platform, location_code)
        cache_file = self.cache_dir / f"expansion_{cache_key}.json"
        
        if cache_file.exists():
            # Check if cache is still valid
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - file_time < self.cache_ttl:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        return None
    
    def _cache_expansion(
        self,
        seed_term: str,
        platform: str,
        location_code: int,
        suggestions: List[Dict[str, Any]]
    ):
        """Cache expansion results."""
        if not self.cache_dir:
            return
        
        cache_key = self._get_cache_key('expansion', seed_term, platform, location_code)
        cache_file = self.cache_dir / f"expansion_{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(suggestions, f)
    
    def _get_cached_metrics(
        self,
        keywords: List[str],
        platform: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get cached metrics for keywords."""
        if not self.cache_dir:
            return {}
        
        cached_metrics = {}
        for keyword in keywords:
            cache_key = self._get_cache_key('metrics', keyword, platform)
            cache_file = self.cache_dir / f"metrics_{cache_key}.json"
            
            if cache_file.exists():
                # Check if cache is still valid
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - file_time < self.cache_ttl:
                    with open(cache_file, 'r') as f:
                        cached_metrics[keyword] = json.load(f)
        
        return cached_metrics
    
    def _cache_metrics(
        self,
        keyword: str,
        platform: str,
        metrics: Dict[str, Any]
    ):
        """Cache metrics for a keyword."""
        if not self.cache_dir:
            return
        
        cache_key = self._get_cache_key('metrics', keyword, platform)
        cache_file = self.cache_dir / f"metrics_{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(metrics, f)