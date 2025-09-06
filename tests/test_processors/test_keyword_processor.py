"""
Unit tests for KeywordProcessor module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
import json
import tempfile
from datetime import datetime, timedelta

from src.processors.keyword_processor import KeywordProcessor
from models.keyword_models import ExpandedKeyword
from models.location_models import Location


class TestKeywordProcessor:
    """Test suite for KeywordProcessor class."""
    
    @pytest.fixture
    def mock_google_client(self):
        """Create mock Google Ads client."""
        client = Mock()
        client.get_keywords_for_keywords = MagicMock()
        client.get_search_volume = MagicMock()
        return client
    
    @pytest.fixture
    def mock_bing_client(self):
        """Create mock Bing Ads client."""
        client = Mock()
        client.get_keywords_for_keywords = MagicMock()
        client.get_search_volume = MagicMock()
        return client
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def processor_with_cache(self, mock_google_client, mock_bing_client, temp_cache_dir):
        """Create KeywordProcessor with caching enabled."""
        return KeywordProcessor(
            google_ads_client=mock_google_client,
            bing_ads_client=mock_bing_client,
            cache_dir=temp_cache_dir,
            cache_ttl_hours=1
        )
    
    @pytest.fixture
    def processor_no_cache(self, mock_google_client, mock_bing_client):
        """Create KeywordProcessor without caching."""
        return KeywordProcessor(
            google_ads_client=mock_google_client,
            bing_ads_client=mock_bing_client,
            cache_dir=None
        )
    
    @pytest.fixture
    def sample_seed_keywords(self):
        """Sample seed keywords for testing."""
        return [
            {'keyword': 'plumber', 'category': 'service'},
            {'keyword': 'emergency plumber', 'category': 'emergency'},
            {'keyword': 'drain cleaning', 'category': 'repair'}
        ]
    
    @pytest.fixture
    def sample_locations(self):
        """Sample locations for testing."""
        return [
            Location(city='Dallas', state='TX', zip_code='75201'),
            Location(city='Austin', state='TX', zip_code='78701'),
            Location(city='Houston', state='TX', zip_code='77001')
        ]
    
    def test_initialization(self, mock_google_client, mock_bing_client, temp_cache_dir):
        """Test processor initialization."""
        processor = KeywordProcessor(
            google_ads_client=mock_google_client,
            bing_ads_client=mock_bing_client,
            cache_dir=temp_cache_dir,
            cache_ttl_hours=24
        )
        
        assert processor.google_ads_client == mock_google_client
        assert processor.bing_ads_client == mock_bing_client
        assert processor.cache_dir == temp_cache_dir
        assert processor.cache_ttl == timedelta(hours=24)
        assert temp_cache_dir.exists()
    
    def test_expand_seed_keywords_google_ads(self, processor_no_cache, sample_seed_keywords):
        """Test keyword expansion with Google Ads."""
        # Mock API response
        processor_no_cache.google_ads_client.get_keywords_for_keywords.return_value = {
            'tasks': [{
                'result': [
                    {
                        'keyword': 'plumber near me',
                        'search_volume': 1000,
                        'competition': 0.8,
                        'cpc': 5.50
                    },
                    {
                        'keyword': 'local plumber',
                        'search_volume': 800,
                        'competition': 0.7,
                        'cpc': 4.50
                    }
                ]
            }]
        }
        
        # Expand keywords
        expanded = processor_no_cache.expand_seed_keywords(
            sample_seed_keywords[:1],  # Just first seed
            platform='google_ads',
            location_code=2840
        )
        
        # Assertions
        assert len(expanded) == 3  # 2 suggestions + 1 seed
        assert any(k.keyword == 'plumber near me' for k in expanded)
        assert any(k.keyword == 'local plumber' for k in expanded)
        assert any(k.keyword == 'plumber' for k in expanded)  # Original seed
        
        # Check that all have correct attributes
        for keyword in expanded:
            assert keyword.seed_keyword == 'plumber'
            assert keyword.category == 'service'
            assert keyword.platform == 'google_ads'
            assert keyword.location_code == 2840
    
    def test_expand_seed_keywords_bing_ads(self, processor_no_cache, sample_seed_keywords):
        """Test keyword expansion with Bing Ads."""
        # Mock API response
        processor_no_cache.bing_ads_client.get_keywords_for_keywords.return_value = {
            'tasks': [{
                'result': [
                    {
                        'keyword': '24 hour plumber',
                        'search_volume': 500,
                        'competition': 0.6,
                        'bid': 6.00
                    }
                ]
            }]
        }
        
        # Expand keywords
        expanded = processor_no_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='bing_ads',
            location_code=2840
        )
        
        # Assertions
        assert len(expanded) == 2  # 1 suggestion + 1 seed
        assert any(k.keyword == '24 hour plumber' for k in expanded)
        assert expanded[0].platform == 'bing_ads'
    
    def test_expand_with_caching(self, processor_with_cache, sample_seed_keywords):
        """Test that caching works for expansion."""
        # Mock API response
        api_response = {
            'tasks': [{
                'result': [
                    {
                        'keyword': 'test keyword',
                        'search_volume': 100,
                        'competition': 0.5,
                        'cpc': 2.00
                    }
                ]
            }]
        }
        processor_with_cache.google_ads_client.get_keywords_for_keywords.return_value = api_response
        
        # First call - should hit API
        expanded1 = processor_with_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='google_ads'
        )
        
        # Second call - should use cache
        expanded2 = processor_with_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='google_ads'
        )
        
        # API should only be called once
        assert processor_with_cache.google_ads_client.get_keywords_for_keywords.call_count == 1
        assert len(expanded1) == len(expanded2)
    
    def test_combine_with_locations(self, processor_no_cache, sample_locations):
        """Test combining keywords with locations."""
        # Create sample keywords
        keywords = [
            ExpandedKeyword(
                keyword='plumber',
                seed_keyword='plumber',
                category='service',
                search_volume=1000,
                competition=0.8,
                cpc=5.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='drain cleaning',
                seed_keyword='drain cleaning',
                category='repair',
                search_volume=500,
                competition=0.6,
                cpc=4.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            )
        ]
        
        # Combine with locations
        combined = processor_no_cache.combine_with_locations(keywords, sample_locations)
        
        # Should have combinations for each keyword with each location type
        # 2 keywords * 3 locations * (city + city_state + zip + near_zip) + 2 near me
        assert len(combined) > len(keywords)
        
        # Check for specific patterns (keywords are lowercased)
        assert any('plumber in dallas' in k.keyword for k in combined)
        assert any('plumber dallas tx' in k.keyword for k in combined)
        assert any('plumber 75201' in k.keyword for k in combined)
        assert any('plumber near 75201' in k.keyword for k in combined)
        assert any('plumber near me' in k.keyword for k in combined)
        
        # Check location metadata
        dallas_keywords = [k for k in combined if 'dallas' in k.keyword]
        assert all(k.location_value for k in dallas_keywords)
    
    def test_enrich_keywords_with_metrics_google(self, processor_no_cache):
        """Test enriching keywords with Google Ads metrics."""
        # Create keywords without metrics
        keywords = [
            ExpandedKeyword(
                keyword='plumber near me',
                seed_keyword='plumber',
                category='service',
                search_volume=0,
                competition=0,
                cpc=0,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='emergency plumber',
                seed_keyword='plumber',
                category='emergency',
                search_volume=0,
                competition=0,
                cpc=0,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            )
        ]
        
        # Mock API response
        processor_no_cache.google_ads_client.get_search_volume.return_value = {
            'tasks': [{
                'result': [
                    {
                        'keyword': 'plumber near me',
                        'search_volume': 1500,
                        'competition': 0.85,
                        'cpc': 6.50
                    },
                    {
                        'keyword': 'emergency plumber',
                        'search_volume': 800,
                        'competition': 0.9,
                        'cpc': 8.00
                    }
                ]
            }]
        }
        
        # Enrich keywords
        enriched = processor_no_cache.enrich_keywords_with_metrics(
            keywords,
            platform='google_ads',
            batch_size=10
        )
        
        # Check that metrics were added
        assert len(enriched) == 2
        
        plumber_near = next(k for k in enriched if k.keyword == 'plumber near me')
        assert plumber_near.search_volume == 1500
        assert plumber_near.competition == 0.85
        assert plumber_near.cpc == 6.50
        
        emergency = next(k for k in enriched if k.keyword == 'emergency plumber')
        assert emergency.search_volume == 800
        assert emergency.competition == 0.9
        assert emergency.cpc == 8.00
    
    def test_categorize_keywords(self, processor_no_cache):
        """Test keyword categorization."""
        # Create uncategorized keywords
        keywords = [
            ExpandedKeyword(
                keyword='emergency plumber 24/7',
                seed_keyword='plumber',
                category='general',
                search_volume=500,
                competition=0.8,
                cpc=7.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='plumber repair service',
                seed_keyword='plumber',
                category='general',
                search_volume=300,
                competition=0.6,
                cpc=5.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='commercial plumber installation',
                seed_keyword='plumber',
                category='general',
                search_volume=200,
                competition=0.7,
                cpc=6.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='how much does plumber cost',
                seed_keyword='plumber',
                category='general',
                search_volume=1000,
                competition=0.3,
                cpc=2.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            )
        ]
        
        # Categorize
        categorized = processor_no_cache.categorize_keywords(keywords)
        
        # Check categories (categorization stops at first match, so 'commercial plumber installation' becomes 'installation')
        assert any(k.category == 'emergency' for k in categorized)
        assert any(k.category == 'repair' for k in categorized)
        assert any(k.category == 'installation' for k in categorized)  # 'commercial plumber installation' matches 'installation' first
        assert any(k.category == 'informational' for k in categorized)
    
    def test_filter_keywords(self, processor_no_cache):
        """Test keyword filtering."""
        # Create keywords with various metrics
        keywords = [
            ExpandedKeyword(
                keyword='plumber',
                seed_keyword='plumber',
                category='service',
                search_volume=5,  # Below threshold
                competition=0.5,
                cpc=5.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='emergency plumber',
                seed_keyword='plumber',
                category='emergency',
                search_volume=1000,
                competition=0.8,
                cpc=150.00,  # Above CPC threshold
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='local plumber',
                seed_keyword='plumber',
                category='service',
                search_volume=500,
                competition=0.6,
                cpc=6.00,  # Should pass all filters
                platform='google_ads',
                location_code=2840,
                language_code='en'
            ),
            ExpandedKeyword(
                keyword='free plumber',
                seed_keyword='plumber',
                category='service',
                search_volume=100,
                competition=0.3,
                cpc=1.00,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            )
        ]
        
        # Filter keywords
        filtered = processor_no_cache.filter_keywords(
            keywords,
            min_search_volume=10,
            max_cpc=100.0,
            max_competition=0.8,
            exclude_patterns=['free']
        )
        
        # Should only have 'local plumber'
        assert len(filtered) == 1
        assert filtered[0].keyword == 'local plumber'
    
    def test_batch_processing(self, processor_no_cache):
        """Test batch processing for large keyword sets."""
        # Create many keywords
        keywords = []
        for i in range(250):  # More than default batch size
            keywords.append(
                ExpandedKeyword(
                    keyword=f'keyword_{i}',
                    seed_keyword='seed',
                    category='general',
                    search_volume=0,
                    competition=0,
                    cpc=0,
                    platform='google_ads',
                    location_code=2840,
                    language_code='en'
                )
            )
        
        # Mock API to return metrics for all
        def mock_search_volume(keywords):
            result = []
            for kw in keywords:
                result.append({
                    'keyword': kw,
                    'search_volume': 100,
                    'competition': 0.5,
                    'cpc': 3.00
                })
            return {'tasks': [{'result': result}]}
        
        processor_no_cache.google_ads_client.get_search_volume.side_effect = mock_search_volume
        
        # Enrich with batching
        enriched = processor_no_cache.enrich_keywords_with_metrics(
            keywords,
            platform='google_ads',
            batch_size=100
        )
        
        # Should have called API 3 times (250 keywords / 100 batch size)
        assert processor_no_cache.google_ads_client.get_search_volume.call_count == 3
        assert len(enriched) == 250
        assert all(k.search_volume == 100 for k in enriched)
    
    def test_error_handling_expansion(self, processor_no_cache, sample_seed_keywords):
        """Test error handling during keyword expansion."""
        # Mock API to raise exception
        processor_no_cache.google_ads_client.get_keywords_for_keywords.side_effect = Exception("API Error")
        
        # Should handle error gracefully
        expanded = processor_no_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='google_ads'
        )
        
        # Should still include seed keyword
        assert len(expanded) == 1
        assert expanded[0].keyword == 'plumber'
    
    def test_error_handling_metrics(self, processor_no_cache):
        """Test error handling during metric enrichment."""
        keywords = [
            ExpandedKeyword(
                keyword='test keyword',
                seed_keyword='test',
                category='general',
                search_volume=0,
                competition=0,
                cpc=0,
                platform='google_ads',
                location_code=2840,
                language_code='en'
            )
        ]
        
        # Mock API to raise exception
        processor_no_cache.google_ads_client.get_search_volume.side_effect = Exception("API Error")
        
        # Should handle error gracefully
        enriched = processor_no_cache.enrich_keywords_with_metrics(keywords)
        
        # Should return keywords without metrics
        assert len(enriched) == 1
        assert enriched[0].search_volume == 0
    
    def test_cache_expiry(self, processor_with_cache, sample_seed_keywords):
        """Test that expired cache is not used."""
        # Mock API response
        api_response = {
            'tasks': [{
                'result': [
                    {
                        'keyword': 'cached keyword',
                        'search_volume': 100,
                        'competition': 0.5,
                        'cpc': 2.00
                    }
                ]
            }]
        }
        processor_with_cache.google_ads_client.get_keywords_for_keywords.return_value = api_response
        
        # Set cache TTL to 0 to expire immediately
        processor_with_cache.cache_ttl = timedelta(seconds=0)
        
        # First call
        expanded1 = processor_with_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='google_ads'
        )
        
        # Second call - should hit API again due to expired cache
        expanded2 = processor_with_cache.expand_seed_keywords(
            sample_seed_keywords[:1],
            platform='google_ads'
        )
        
        # API should be called twice
        assert processor_with_cache.google_ads_client.get_keywords_for_keywords.call_count == 2
    
    def test_empty_seed_keywords(self, processor_no_cache):
        """Test handling of empty seed keywords."""
        # Empty list
        expanded = processor_no_cache.expand_seed_keywords([])
        assert expanded == []
        
        # List with empty keyword
        expanded = processor_no_cache.expand_seed_keywords([{'keyword': '', 'category': 'test'}])
        assert expanded == []
    
    def test_duplicate_removal(self, processor_no_cache):
        """Test that duplicate keywords are removed during expansion."""
        # Mock API to return duplicates
        processor_no_cache.google_ads_client.get_keywords_for_keywords.return_value = {
            'tasks': [{
                'result': [
                    {'keyword': 'duplicate', 'search_volume': 100, 'competition': 0.5, 'cpc': 3.00},
                    {'keyword': 'duplicate', 'search_volume': 100, 'competition': 0.5, 'cpc': 3.00},
                    {'keyword': 'unique', 'search_volume': 200, 'competition': 0.6, 'cpc': 4.00}
                ]
            }]
        }
        
        expanded = processor_no_cache.expand_seed_keywords(
            [{'keyword': 'test', 'category': 'general'}],
            platform='google_ads'
        )
        
        # Should have no duplicates
        keyword_terms = [k.keyword for k in expanded]
        assert len(keyword_terms) == len(set(keyword_terms))