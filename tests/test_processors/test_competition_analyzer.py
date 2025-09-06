"""
Tests for Competition Analyzer Module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import json
from datetime import datetime

from src.processors.competition_analyzer import CompetitionAnalyzer
from src.processors.landing_page_scraper import LandingPageScraper
from models.competition_models import (
    CompetitorDomain,
    CompetitorKeyword,
    KeywordGap,
    ScrapedCopy,
    CompetitorAnalysis
)
from models.keyword_models import Keyword, KeywordMetrics


class TestCompetitionAnalyzer:
    """Test suite for CompetitionAnalyzer class."""
    
    @pytest.fixture
    def mock_google_ads_client(self):
        """Create mock Google Ads client."""
        client = AsyncMock()
        return client
    
    @pytest.fixture
    def analyzer(self, mock_google_ads_client, tmp_path):
        """Create CompetitionAnalyzer instance with mocked dependencies."""
        return CompetitionAnalyzer(
            google_ads_client=mock_google_ads_client,
            cache_dir=tmp_path / "cache"
        )
    
    @pytest.mark.asyncio
    async def test_analyze_competitor_website_success(self, analyzer, mock_google_ads_client):
        """Test successful competitor website analysis."""
        # Mock API response
        mock_response = {
            'tasks': [{
                'result': [
                    {
                        'keyword': 'plumbing services',
                        'search_volume': 5000,
                        'cpc': 3.50,
                        'competition': 0.7,
                        'position': 5,
                        'is_paid': False,
                        'estimated_traffic': 250
                    },
                    {
                        'keyword': 'emergency plumber',
                        'search_volume': 8000,
                        'cpc': 5.00,
                        'competition': 0.9,
                        'position': 3,
                        'is_paid': True,
                        'estimated_traffic': 400
                    }
                ]
            }]
        }
        mock_google_ads_client.get_keywords_for_site.return_value = mock_response
        
        # Analyze competitor
        result = await analyzer.analyze_competitor_website(
            competitor_url="https://competitor.com",
            location_code=2840,
            limit=100
        )
        
        # Assertions
        assert isinstance(result, CompetitorDomain)
        assert result.domain == "competitor.com"
        assert result.organic_keywords == 1
        assert result.paid_keywords == 1
        assert result.traffic_estimate == 650
        
        # Verify API was called correctly
        mock_google_ads_client.get_keywords_for_site.assert_called_once_with(
            target="https://competitor.com",
            location_code=2840,
            language_code="en",
            include_branded_keywords=True,
            include_non_branded_keywords=True,
            limit=100
        )
    
    @pytest.mark.asyncio
    async def test_analyze_competitor_website_with_cache(self, analyzer, mock_google_ads_client):
        """Test competitor analysis with caching."""
        # First call - should hit API
        mock_response = {
            'tasks': [{
                'result': [{
                    'keyword': 'test keyword',
                    'search_volume': 1000,
                    'cpc': 2.00,
                    'competition': 0.5
                }]
            }]
        }
        mock_google_ads_client.get_keywords_for_site.return_value = mock_response
        
        result1 = await analyzer.analyze_competitor_website("https://cached.com")
        assert mock_google_ads_client.get_keywords_for_site.call_count == 1
        
        # Second call - should use cache
        result2 = await analyzer.analyze_competitor_website("https://cached.com")
        assert mock_google_ads_client.get_keywords_for_site.call_count == 1  # No additional call
        
        # Results should be the same
        assert result1.domain == result2.domain
        assert result1.organic_keywords == result2.organic_keywords
    
    @pytest.mark.asyncio
    async def test_analyze_competitor_website_error_handling(self, analyzer, mock_google_ads_client):
        """Test error handling in competitor analysis."""
        # Mock API error
        mock_google_ads_client.get_keywords_for_site.side_effect = Exception("API Error")
        
        # Should raise the exception
        with pytest.raises(Exception, match="API Error"):
            await analyzer.analyze_competitor_website("https://error.com")
    
    def test_identify_keyword_gaps_missing_keywords(self, analyzer):
        """Test identification of missing keywords."""
        # Our keywords
        our_keywords = ["plumber", "plumbing repair"]
        
        # Competitor keywords
        competitor_keywords = [
            CompetitorKeyword(
                keyword=Keyword(
                    term="emergency plumber",
                    metrics=KeywordMetrics(search_volume=5000, cpc=4.00, competition=0.8)
                ),
                competitor_domain="competitor.com",
                position=3,
                estimated_traffic=300
            ),
            CompetitorKeyword(
                keyword=Keyword(
                    term="24/7 plumbing",
                    metrics=KeywordMetrics(search_volume=3000, cpc=3.50, competition=0.7)
                ),
                competitor_domain="competitor.com",
                position=5,
                estimated_traffic=150
            ),
            CompetitorKeyword(
                keyword=Keyword(
                    term="plumber",  # We have this one
                    metrics=KeywordMetrics(search_volume=10000, cpc=5.00, competition=0.9)
                ),
                competitor_domain="competitor.com",
                position=2,
                estimated_traffic=500
            )
        ]
        
        # Identify gaps
        gaps = analyzer.identify_keyword_gaps(
            our_keywords=our_keywords,
            competitor_keywords=competitor_keywords,
            our_domain="our-site.com"
        )
        
        # Should find 2 missing keywords
        assert len(gaps) == 2
        assert all(gap.gap_type == "missing" for gap in gaps)
        
        # Check specific gaps
        gap_terms = [gap.keyword.term for gap in gaps]
        assert "emergency plumber" in gap_terms
        assert "24/7 plumbing" in gap_terms
        assert "plumber" not in gap_terms  # We have this one
        
        # Check gap details
        emergency_gap = next(g for g in gaps if g.keyword.term == "emergency plumber")
        assert emergency_gap.best_competitor_position == 3
        assert emergency_gap.potential_traffic == 300
        assert emergency_gap.priority >= 1
    
    def test_calculate_opportunity_scores(self, analyzer):
        """Test opportunity score calculation."""
        gaps = [
            KeywordGap(
                keyword=Keyword(
                    term="high value keyword",
                    metrics=KeywordMetrics(search_volume=10000, cpc=5.00, competition=0.3)
                ),
                our_domain="our-site.com",
                competitor_domains=["competitor.com"],
                gap_type="missing",
                best_competitor_position=2,
                recommendation="Add this keyword",
                priority=5,
                potential_traffic=1500
            ),
            KeywordGap(
                keyword=Keyword(
                    term="low value keyword",
                    metrics=KeywordMetrics(search_volume=100, cpc=1.00, competition=0.9)
                ),
                our_domain="our-site.com",
                competitor_domains=["competitor.com"],
                gap_type="underperforming",
                our_position=50,
                best_competitor_position=30,
                recommendation="Improve ranking",
                priority=2,
                potential_traffic=10
            )
        ]
        
        # Calculate scores
        scored_gaps = analyzer.calculate_opportunity_scores(gaps)
        
        # Should be sorted by score
        assert len(scored_gaps) == 2
        assert scored_gaps[0][1] > scored_gaps[1][1]  # First has higher score
        
        # High value keyword should score higher
        assert scored_gaps[0][0].keyword.term == "high value keyword"
    
    @pytest.mark.asyncio
    async def test_scrape_competitor_landing_pages(self, analyzer):
        """Test landing page scraping."""
        # Mock the landing scraper
        with patch.object(analyzer.landing_scraper, 'scrape_url') as mock_scrape:
            # Setup mock responses
            mock_scrape.side_effect = [
                ScrapedCopy(
                    url="https://page1.com",
                    headline="Best Plumbing Services",
                    cta="Get Free Quote",
                    scrape_success=True
                ),
                ScrapedCopy(
                    url="https://page2.com",
                    headline="24/7 Emergency Plumber",
                    cta="Call Now",
                    scrape_success=True
                ),
                ScrapedCopy(
                    url="https://page3.com",
                    scrape_success=False,
                    error_message="Timeout"
                )
            ]
            
            # Scrape pages
            results = await analyzer.scrape_competitor_landing_pages(
                urls=["https://page1.com", "https://page2.com", "https://page3.com"],
                max_concurrent=2
            )
            
            # Verify results
            assert len(results) == 3
            assert results[0].scrape_success is True
            assert results[0].headline == "Best Plumbing Services"
            assert results[1].scrape_success is True
            assert results[2].scrape_success is False
            assert results[2].error_message == "Timeout"
            
            # Verify scraper was called
            assert mock_scrape.call_count == 3
    
    def test_process_spyfu_data(self, analyzer):
        """Test SpyFu data processing."""
        spyfu_data = {
            'keywords': [
                {
                    'keyword': 'plumber near me',
                    'volume': 20000,
                    'cpc': 4.50,
                    'difficulty': 75,
                    'position': 4,
                    'clicks': 500,
                    'domain': 'competitor.com'
                },
                {
                    'keyword': 'emergency plumbing',
                    'volume': 8000,
                    'cpc': 5.00,
                    'difficulty': 85,
                    'position': 2,
                    'clicks': 350
                }
            ]
        }
        
        # Process data
        result = analyzer.process_spyfu_data(spyfu_data)
        
        # Verify processing
        assert len(result) == 2
        assert all(isinstance(ck, CompetitorKeyword) for ck in result)
        
        # Check first keyword
        first = result[0]
        assert first.keyword.term == 'plumber near me'
        assert first.keyword.metrics.search_volume == 20000
        assert first.keyword.metrics.cpc == 4.50
        assert first.keyword.metrics.competition == 0.75  # difficulty/100
        assert first.competitor_domain == 'competitor.com'
        assert first.position == 4
        assert first.estimated_traffic == 500
    
    def test_generate_competitor_analysis(self, analyzer):
        """Test comprehensive competitor analysis generation."""
        # Setup test data
        competitors = [
            CompetitorDomain(
                domain="competitor1.com",
                organic_keywords=100,
                paid_keywords=50,
                traffic_estimate=5000
            ),
            CompetitorDomain(
                domain="competitor2.com",
                organic_keywords=80,
                paid_keywords=30,
                traffic_estimate=3000
            )
        ]
        
        competitor_keywords = [
            CompetitorKeyword(
                keyword=Keyword(term="keyword1"),
                competitor_domain="competitor1.com",
                position=5
            ),
            CompetitorKeyword(
                keyword=Keyword(term="keyword2"),
                competitor_domain="competitor2.com",
                position=3
            )
        ]
        
        keyword_gaps = [
            KeywordGap(
                keyword=Keyword(term="gap1"),
                our_domain="our-site.com",
                competitor_domains=["competitor1.com"],
                gap_type="missing",
                recommendation="Add this keyword",
                priority=5
            )
        ]
        
        scraped_pages = [
            ScrapedCopy(
                url="https://competitor1.com",
                cta="Get Started",
                features=["Fast Service", "24/7 Support"],
                scrape_success=True
            )
        ]
        
        # Generate analysis
        analysis = analyzer.generate_competitor_analysis(
            our_domain="our-site.com",
            competitors=competitors,
            competitor_keywords=competitor_keywords,
            keyword_gaps=keyword_gaps,
            scraped_pages=scraped_pages
        )
        
        # Verify analysis
        assert isinstance(analysis, CompetitorAnalysis)
        assert analysis.our_domain == "our-site.com"
        assert len(analysis.competitors) == 2
        assert len(analysis.competitor_keywords) == 2
        assert len(analysis.keyword_gaps) == 1
        assert len(analysis.recommendations) > 0
        
        # Check summary stats
        stats = analysis.summary_stats
        assert stats['total_competitors_analyzed'] == 2
        assert stats['total_competitor_keywords'] == 2
        assert stats['total_gaps_identified'] == 1
        assert stats['pages_scraped'] == 1
        assert stats['avg_competitor_traffic'] == 4000.0
    
    def test_generate_recommendations(self, analyzer):
        """Test recommendation generation."""
        # Create test gaps
        gaps = [
            KeywordGap(
                keyword=Keyword(
                    term="high volume keyword",
                    metrics=KeywordMetrics(search_volume=5000, competition=0.2)
                ),
                our_domain="our-site.com",
                competitor_domains=["competitor.com"],
                gap_type="missing",
                recommendation="Add keyword",
                priority=5
            ),
            KeywordGap(
                keyword=Keyword(
                    term="low competition keyword",
                    metrics=KeywordMetrics(search_volume=1000, competition=0.1)
                ),
                our_domain="our-site.com",
                competitor_domains=["competitor.com"],
                gap_type="missing",
                recommendation="Easy win",
                priority=4
            )
        ]
        
        scraped_pages = [
            ScrapedCopy(
                url="https://competitor.com",
                cta="Start Free Trial",
                features=["Feature 1", "Feature 2"],
                scrape_success=True
            )
        ]
        
        # Generate recommendations
        recommendations = analyzer._generate_recommendations(gaps, scraped_pages)
        
        # Should have recommendations
        assert len(recommendations) > 0
        
        # Check for expected recommendation types
        rec_text = ' '.join(recommendations)
        assert 'keyword opportunities' in rec_text.lower()
        assert any('cta' in r.lower() for r in recommendations)
    
    def test_calculate_priority(self, analyzer):
        """Test priority calculation based on metrics."""
        # High volume, low competition = high priority
        metrics1 = KeywordMetrics(search_volume=15000, competition=0.2)
        priority1 = analyzer._calculate_priority(metrics1)
        assert priority1 >= 4
        
        # Low volume, high competition = low priority
        metrics2 = KeywordMetrics(search_volume=100, competition=0.9)
        priority2 = analyzer._calculate_priority(metrics2)
        assert priority2 <= 2
        
        # No metrics = lowest priority
        priority3 = analyzer._calculate_priority(None)
        assert priority3 == 1
        
        # Max priority should be 5
        metrics4 = KeywordMetrics(search_volume=100000, competition=0.1)
        priority4 = analyzer._calculate_priority(metrics4)
        assert priority4 == 5
    
    def test_cache_operations(self, analyzer):
        """Test cache save and load operations."""
        # Test data
        test_data = {
            'domain': 'test.com',
            'keywords': 100,
            'traffic': 5000
        }
        
        # Save to cache
        analyzer._save_to_cache('test_key', test_data)
        
        # Load from cache
        loaded_data = analyzer._load_from_cache('test_key')
        
        # Should match
        assert loaded_data == test_data
        
        # Test expired cache (modify file time)
        cache_file = analyzer.cache_dir / 'test_key.json'
        if cache_file.exists():
            # Set file time to 25 hours ago
            import os
            import time
            old_time = time.time() - (25 * 3600)
            os.utime(cache_file, (old_time, old_time))
            
            # Should return None for expired cache
            expired_data = analyzer._load_from_cache('test_key')
            assert expired_data is None
    
    def test_get_top_opportunities(self):
        """Test getting top opportunities from analysis."""
        # Create analysis with gaps
        gaps = [
            KeywordGap(
                keyword=Keyword(term=f"keyword{i}"),
                our_domain="our-site.com",
                competitor_domains=["competitor.com"],
                gap_type="missing",
                recommendation=f"Recommendation {i}",
                priority=5-i,
                potential_traffic=1000*(5-i)
            )
            for i in range(5)
        ]
        
        analysis = CompetitorAnalysis(
            our_domain="our-site.com",
            competitors=[],
            competitor_keywords=[],
            keyword_gaps=gaps,
            overlap_keywords=[],
            unique_keywords=[]
        )
        
        # Get top 3 opportunities
        top_opps = analysis.get_top_opportunities(limit=3)
        
        # Should return top 3 by score
        assert len(top_opps) == 3
        # Verify they're sorted by opportunity score
        scores = [gap.calculate_opportunity_score() for gap in top_opps]
        assert scores == sorted(scores, reverse=True)