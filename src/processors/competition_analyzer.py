"""
Competition Analyzer Module

Analyzes competitor websites and keywords using DataForSEO APIs and SpyFu data.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import json
from urllib.parse import urlparse

from api_integration.dataforseo.google_ads_client import GoogleAdsClient
from models.competition_models import (
    CompetitorDomain,
    CompetitorKeyword,
    KeywordGap,
    SpyFuData,
    ScrapedCopy,
    CompetitorAnalysis
)
from models.keyword_models import Keyword, KeywordMetrics
from src.processors.landing_page_scraper import LandingPageScraper

logger = logging.getLogger(__name__)


class CompetitionAnalyzer:
    """
    Analyzes competition using various data sources including DataForSEO and SpyFu.
    """
    
    def __init__(
        self,
        google_ads_client: GoogleAdsClient,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize CompetitionAnalyzer with API client and optional caching.
        
        Args:
            google_ads_client: Google Ads API client for DataForSEO
            cache_dir: Optional directory for caching results
        """
        self.google_ads_client = google_ads_client
        self.landing_scraper = LandingPageScraper()
        self.cache_dir = cache_dir
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("CompetitionAnalyzer initialized")
    
    async def analyze_competitor_website(
        self,
        competitor_url: str,
        location_code: int = 2840,  # Default: USA
        language_code: str = "en",
        include_branded: bool = True,
        include_non_branded: bool = True,
        limit: int = 500
    ) -> CompetitorDomain:
        """
        Analyze a competitor website using DataForSEO Keywords for Site endpoint.
        
        Args:
            competitor_url: URL of competitor website
            location_code: Target location code
            language_code: Target language code
            include_branded: Include branded keywords
            include_non_branded: Include non-branded keywords
            limit: Maximum number of keywords to retrieve
        
        Returns:
            CompetitorDomain object with analysis results
        """
        logger.info(f"Analyzing competitor website: {competitor_url}")
        
        # Parse and clean URL
        parsed_url = urlparse(competitor_url)
        domain = parsed_url.netloc or parsed_url.path
        domain = domain.replace('www.', '')
        
        try:
            # Check cache first
            cached_result = self._load_from_cache(f"competitor_{domain}")
            if cached_result:
                logger.info(f"Using cached analysis for {domain}")
                return CompetitorDomain(**cached_result)
            
            # Call DataForSEO Keywords for Site API
            response = await self.google_ads_client.get_keywords_for_site(
                target=competitor_url,
                location_code=location_code,
                language_code=language_code,
                include_branded_keywords=include_branded,
                include_non_branded_keywords=include_non_branded,
                limit=limit
            )
            
            # Process response
            keywords = []
            total_traffic = 0
            
            if response and 'tasks' in response:
                for task in response['tasks']:
                    if task.get('result'):
                        for item in task['result']:
                            keyword_data = CompetitorKeyword(
                                keyword=Keyword(
                                    term=item.get('keyword', ''),
                                    metrics=KeywordMetrics(
                                        search_volume=item.get('search_volume', 0),
                                        cpc=item.get('cpc', 0),
                                        competition=item.get('competition', 0)
                                    )
                                ),
                                competitor_domain=domain,
                                position=item.get('position', None),
                                is_paid=item.get('is_paid', False),
                                estimated_traffic=item.get('estimated_traffic', 0)
                            )
                            keywords.append(keyword_data)
                            total_traffic += keyword_data.estimated_traffic or 0
            
            # Create CompetitorDomain object
            competitor = CompetitorDomain(
                domain=domain,
                url=competitor_url,
                organic_keywords=len([k for k in keywords if not k.is_paid]),
                paid_keywords=len([k for k in keywords if k.is_paid]),
                traffic_estimate=int(total_traffic),
                metadata={
                    'location_code': location_code,
                    'language_code': language_code,
                    'keywords_analyzed': len(keywords)
                }
            )
            
            # Cache the result
            self._save_to_cache(f"competitor_{domain}", competitor.dict())
            
            # Store keywords for later use
            self._competitor_keywords = keywords
            
            logger.info(f"Analyzed {domain}: {len(keywords)} keywords, "
                       f"{competitor.traffic_estimate} estimated traffic")
            
            return competitor
            
        except Exception as e:
            logger.error(f"Error analyzing competitor {domain}: {e}")
            raise
    
    def identify_keyword_gaps(
        self,
        our_keywords: List[str],
        competitor_keywords: List[CompetitorKeyword],
        our_domain: str = "our-site.com"
    ) -> List[KeywordGap]:
        """
        Identify keyword gaps between our site and competitors.
        
        Args:
            our_keywords: List of our current keywords
            competitor_keywords: List of competitor keywords
            our_domain: Our domain name
        
        Returns:
            List of KeywordGap objects
        """
        logger.info("Identifying keyword gaps")
        
        # Convert our keywords to set for faster lookup
        our_keyword_set = set(k.lower() for k in our_keywords)
        
        # Group competitor keywords by term
        competitor_keyword_map = {}
        for ck in competitor_keywords:
            term = ck.keyword.term.lower()
            if term not in competitor_keyword_map:
                competitor_keyword_map[term] = []
            competitor_keyword_map[term].append(ck)
        
        gaps = []
        
        # Find missing keywords (competitors have, we don't)
        for term, comp_keywords in competitor_keyword_map.items():
            if term not in our_keyword_set:
                # Calculate best competitor position
                best_position = min(
                    (ck.position for ck in comp_keywords if ck.position),
                    default=None
                )
                
                # Calculate potential traffic
                potential_traffic = sum(
                    ck.estimated_traffic or 0 for ck in comp_keywords
                )
                
                # Get unique competitor domains
                competitor_domains = list(set(
                    ck.competitor_domain for ck in comp_keywords
                ))
                
                gap = KeywordGap(
                    keyword=comp_keywords[0].keyword,
                    our_domain=our_domain,
                    competitor_domains=competitor_domains,
                    gap_type="missing",
                    our_position=None,
                    best_competitor_position=best_position,
                    recommendation=f"Add '{term}' to your keyword strategy. "
                                 f"Competitors rank position {best_position} with "
                                 f"{potential_traffic} estimated traffic.",
                    priority=self._calculate_priority(
                        comp_keywords[0].keyword.metrics
                    ),
                    potential_traffic=int(potential_traffic)
                )
                gaps.append(gap)
        
        # Sort gaps by opportunity score
        gaps.sort(key=lambda x: x.calculate_opportunity_score(), reverse=True)
        
        logger.info(f"Identified {len(gaps)} keyword gaps")
        return gaps
    
    def _calculate_priority(self, metrics: Optional[KeywordMetrics]) -> int:
        """
        Calculate priority score (1-5) based on keyword metrics.
        
        Args:
            metrics: Keyword metrics
        
        Returns:
            Priority score from 1 (low) to 5 (high)
        """
        if not metrics:
            return 1
        
        score = 1
        
        # Higher search volume = higher priority
        if metrics.search_volume:
            if metrics.search_volume > 10000:
                score += 2
            elif metrics.search_volume > 1000:
                score += 1
        
        # Lower competition = higher priority
        if metrics.competition is not None:
            if metrics.competition < 0.3:
                score += 2
            elif metrics.competition < 0.6:
                score += 1
        
        return min(score, 5)
    
    def calculate_opportunity_scores(
        self,
        keyword_gaps: List[KeywordGap]
    ) -> List[Tuple[KeywordGap, float]]:
        """
        Calculate opportunity scores for keyword gaps.
        
        Args:
            keyword_gaps: List of keyword gaps
        
        Returns:
            List of tuples (gap, score) sorted by score
        """
        scored_gaps = []
        
        for gap in keyword_gaps:
            score = gap.calculate_opportunity_score()
            scored_gaps.append((gap, score))
        
        # Sort by score descending
        scored_gaps.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Calculated opportunity scores for {len(scored_gaps)} gaps")
        return scored_gaps
    
    async def scrape_competitor_landing_pages(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[ScrapedCopy]:
        """
        Scrape competitor landing pages for copy analysis.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent scraping tasks
        
        Returns:
            List of ScrapedCopy objects
        """
        logger.info(f"Scraping {len(urls)} competitor landing pages")
        
        scraped_pages = []
        
        # Process in batches to respect rate limits
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            
            # Create scraping tasks
            tasks = [
                self.landing_scraper.scrape_url(url)
                for url in batch
            ]
            
            # Execute batch
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    logger.error(f"Error scraping {url}: {result}")
                    scraped_pages.append(
                        ScrapedCopy(
                            url=url,
                            scrape_success=False,
                            error_message=str(result)
                        )
                    )
                else:
                    scraped_pages.append(result)
            
            # Small delay between batches
            if i + max_concurrent < len(urls):
                await asyncio.sleep(1)
        
        successful = len([s for s in scraped_pages if s.scrape_success])
        logger.info(f"Successfully scraped {successful}/{len(urls)} pages")
        
        return scraped_pages
    
    def process_spyfu_data(
        self,
        spyfu_data: Dict[str, Any]
    ) -> List[CompetitorKeyword]:
        """
        Process SpyFu export data into CompetitorKeyword objects.
        
        Args:
            spyfu_data: Parsed SpyFu data from CSV
        
        Returns:
            List of CompetitorKeyword objects
        """
        logger.info("Processing SpyFu data")
        
        competitor_keywords = []
        
        keywords = spyfu_data.get('keywords', [])
        
        for kw_data in keywords:
            # Extract domain from data if available
            domain = kw_data.get('domain', 'spyfu-competitor')
            
            # Create Keyword object
            keyword = Keyword(
                term=kw_data.get('keyword', ''),
                metrics=KeywordMetrics(
                    search_volume=kw_data.get('volume', 0),
                    cpc=kw_data.get('cpc', 0),
                    competition=kw_data.get('difficulty', 0) / 100 if kw_data.get('difficulty') else 0
                ),
                source='spyfu'
            )
            
            # Create CompetitorKeyword
            competitor_keyword = CompetitorKeyword(
                keyword=keyword,
                competitor_domain=domain,
                position=kw_data.get('position'),
                is_paid=kw_data.get('cpc', 0) > 0,  # Assume paid if CPC exists
                estimated_traffic=kw_data.get('clicks', 0)
            )
            
            competitor_keywords.append(competitor_keyword)
        
        logger.info(f"Processed {len(competitor_keywords)} keywords from SpyFu data")
        return competitor_keywords
    
    def generate_competitor_analysis(
        self,
        our_domain: str,
        competitors: List[CompetitorDomain],
        competitor_keywords: List[CompetitorKeyword],
        keyword_gaps: List[KeywordGap],
        scraped_pages: Optional[List[ScrapedCopy]] = None
    ) -> CompetitorAnalysis:
        """
        Generate comprehensive competitor analysis report.
        
        Args:
            our_domain: Our domain name
            competitors: List of analyzed competitor domains
            competitor_keywords: All competitor keywords
            keyword_gaps: Identified keyword gaps
            scraped_pages: Optional scraped landing pages
        
        Returns:
            CompetitorAnalysis object with full report
        """
        logger.info("Generating competitor analysis report")
        
        # Identify overlap keywords (we have, competitors also have)
        our_keywords_set = set()  # This would come from our keyword list
        overlap_keywords = []
        unique_keywords = []
        
        for ck in competitor_keywords:
            term = ck.keyword.term.lower()
            if term in our_keywords_set:
                overlap_keywords.append(ck.keyword)
            else:
                unique_keywords.append(ck.keyword)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            keyword_gaps,
            scraped_pages
        )
        
        # Calculate summary statistics
        summary_stats = {
            'total_competitors_analyzed': len(competitors),
            'total_competitor_keywords': len(competitor_keywords),
            'total_gaps_identified': len(keyword_gaps),
            'high_priority_gaps': len([g for g in keyword_gaps if g.priority >= 4]),
            'total_overlap_keywords': len(overlap_keywords),
            'total_unique_keywords': len(unique_keywords),
            'avg_competitor_traffic': sum(c.traffic_estimate or 0 for c in competitors) / len(competitors) if competitors else 0,
            'pages_scraped': len(scraped_pages) if scraped_pages else 0
        }
        
        # Create analysis object
        analysis = CompetitorAnalysis(
            our_domain=our_domain,
            competitors=competitors,
            competitor_keywords=competitor_keywords,
            keyword_gaps=keyword_gaps,
            overlap_keywords=overlap_keywords,
            unique_keywords=unique_keywords,
            recommendations=recommendations,
            summary_stats=summary_stats
        )
        
        logger.info(f"Generated analysis with {len(recommendations)} recommendations")
        return analysis
    
    def _generate_recommendations(
        self,
        keyword_gaps: List[KeywordGap],
        scraped_pages: Optional[List[ScrapedCopy]] = None
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Args:
            keyword_gaps: Identified keyword gaps
            scraped_pages: Optional scraped landing pages
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Top keyword opportunities
        top_gaps = sorted(
            keyword_gaps,
            key=lambda x: x.calculate_opportunity_score(),
            reverse=True
        )[:10]
        
        if top_gaps:
            recommendations.append(
                f"Focus on these top {len(top_gaps)} keyword opportunities: " +
                ", ".join(g.keyword.term for g in top_gaps[:5])
            )
        
        # High volume missing keywords
        high_volume_gaps = [
            g for g in keyword_gaps
            if g.gap_type == "missing" and
            g.keyword.metrics and
            g.keyword.metrics.search_volume > 1000
        ]
        if high_volume_gaps:
            recommendations.append(
                f"You're missing {len(high_volume_gaps)} high-volume keywords "
                f"(>1000 searches/month). Prioritize content creation for these terms."
            )
        
        # Low competition opportunities
        low_comp_gaps = [
            g for g in keyword_gaps
            if g.keyword.metrics and
            g.keyword.metrics.competition < 0.3
        ]
        if low_comp_gaps:
            recommendations.append(
                f"Found {len(low_comp_gaps)} low-competition keyword opportunities. "
                f"These are easier wins for quick ranking improvements."
            )
        
        # Landing page insights
        if scraped_pages:
            successful_scrapes = [s for s in scraped_pages if s.scrape_success]
            if successful_scrapes:
                # Analyze common CTAs
                ctas = []
                for page in successful_scrapes:
                    if page.cta:
                        ctas.append(page.cta)
                
                if ctas:
                    recommendations.append(
                        f"Common competitor CTAs to consider: {', '.join(set(ctas[:3]))}"
                    )
                
                # Analyze features mentioned
                all_features = []
                for page in successful_scrapes:
                    all_features.extend(page.features)
                
                if all_features:
                    recommendations.append(
                        f"Key features highlighted by competitors: {', '.join(set(all_features[:5]))}"
                    )
        
        return recommendations
    
    # Cache management methods
    
    def _load_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Load cached data if available and fresh."""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            # Check if cache is fresh (less than 24 hours old)
            file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            if file_age < 86400:  # 24 hours
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        return None
    
    def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """Save data to cache."""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)