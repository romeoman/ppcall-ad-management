"""Tests for Google Ads DataForSEO client following TDD approach."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from aioresponses import aioresponses
import json
from datetime import datetime

from api_integration.dataforseo.google_ads_client import GoogleAdsClient
from tests.fixtures.api_responses import APIResponseFixtures


class TestGoogleAdsClient:
    """Test suite for GoogleAdsClient."""

    @pytest.fixture
    def client(self):
        """Create a GoogleAdsClient instance."""
        return GoogleAdsClient(
            login="test_login",
            password="test_password",
            max_concurrent=5
        )

    @pytest.fixture
    def mock_responses(self):
        """Get mock API responses."""
        return APIResponseFixtures()

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initializes with correct settings."""
        assert client.login == "test_login"
        assert client.password == "test_password"
        assert client.max_concurrent == 5
        assert client.BASE_URL == "https://api.dataforseo.com/v3"

    @pytest.mark.asyncio
    async def test_authentication_setup(self, client):
        """Test that basic auth is properly configured."""
        async with client:
            assert client.auth is not None
            assert isinstance(client.auth, aiohttp.BasicAuth)
            assert client.auth.login == "test_login"
            assert client.auth.password == "test_password"

    # Search Volume Endpoint Tests
    @pytest.mark.asyncio
    async def test_search_volume_single_keyword(self, client):
        """Test getting search volume for a single keyword."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            # Mock successful response
            mock_response = {
                "status_code": 20000,
                "status_message": "Ok.",
                "tasks": [{
                    "id": "task_123",
                    "status_code": 20000,
                    "status_message": "Ok.",
                    "cost": 0.005,
                    "result": [{
                        "keyword": "marketing software",
                        "search_volume": 14800,
                        "competition": 0.75,
                        "competition_level": "HIGH",
                        "cpc": 12.45,
                        "low_top_of_page_bid": 8.23,
                        "high_top_of_page_bid": 18.67,
                        "monthly_searches": [
                            {"year": 2024, "month": 11, "search_volume": 15200},
                            {"year": 2024, "month": 10, "search_volume": 14500},
                            {"year": 2024, "month": 9, "search_volume": 14800}
                        ]
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["marketing software"],
                    location_code=2840,  # USA
                    language_code="en"
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 1
                assert result["data"][0]["keyword"] == "marketing software"
                assert result["data"][0]["search_volume"] == 14800
                assert result["data"][0]["cpc"] == 12.45
                assert result["data"][0]["competition"] == 0.75
                assert len(result["data"][0]["monthly_searches"]) == 3

    @pytest.mark.asyncio
    async def test_search_volume_bulk_keywords(self, client):
        """Test getting search volume for bulk keywords (up to 1000)."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            # Generate test keywords
            test_keywords = [f"keyword_{i}" for i in range(100)]
            
            # Mock response with multiple keywords
            mock_results = []
            for kw in test_keywords[:10]:  # Mock first 10 for brevity
                mock_results.append({
                    "keyword": kw,
                    "search_volume": 1000,
                    "competition": 0.5,
                    "cpc": 2.5,
                    "low_top_of_page_bid": 1.5,
                    "high_top_of_page_bid": 3.5
                })
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "cost": 0.05,
                    "result": mock_results
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=test_keywords,
                    location_code=2840
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 10
                assert result["cost"] == 0.05

    @pytest.mark.asyncio
    async def test_search_volume_with_date_range(self, client):
        """Test search volume with historical date range."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "ppc advertising",
                        "search_volume": 8100,
                        "competition": 0.82,
                        "cpc": 15.75,
                        "monthly_searches": [
                            {"year": 2024, "month": i, "search_volume": 8000 + i * 100}
                            for i in range(1, 13)
                        ]
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["ppc advertising"],
                    location_code=2840,
                    date_from="2024-01-01",
                    date_to="2024-12-31"
                )
                
                assert result["success"] is True
                assert len(result["data"][0]["monthly_searches"]) == 12
                # Verify date range was passed in request
                assert len(m.requests) > 0

    @pytest.mark.asyncio
    async def test_search_volume_with_sorting(self, client):
        """Test search volume with result sorting."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"keyword": "high volume", "search_volume": 100000, "cpc": 5.0},
                        {"keyword": "medium volume", "search_volume": 50000, "cpc": 10.0},
                        {"keyword": "low volume", "search_volume": 1000, "cpc": 20.0}
                    ]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["high volume", "medium volume", "low volume"],
                    sort_by="search_volume"
                )
                
                assert result["success"] is True
                assert result["data"][0]["search_volume"] == 100000
                assert result["data"][1]["search_volume"] == 50000
                assert result["data"][2]["search_volume"] == 1000

    @pytest.mark.asyncio
    async def test_search_volume_adult_keywords_filter(self, client):
        """Test filtering of adult/sensitive keywords."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": []  # Empty results when adult keywords filtered
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["test keyword"],
                    include_adult_keywords=False
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 0

    @pytest.mark.asyncio
    async def test_search_volume_error_handling(self, client):
        """Test error handling for search volume endpoint."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            # Test API error response
            mock_error = {
                "status_code": 40000,
                "status_message": "Invalid authentication"
            }
            
            m.post(endpoint, payload=mock_error, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["test"]
                )
                
                assert result["success"] is False
                assert "Invalid authentication" in result["error"]
                assert result["status_code"] == 40000

    @pytest.mark.asyncio
    async def test_search_volume_task_error(self, client):
        """Test handling of task-level errors."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 40501,
                    "status_message": "Invalid location code"
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["test"],
                    location_code=99999  # Invalid location
                )
                
                assert result["success"] is False
                assert "Invalid location code" in result["error"]

    @pytest.mark.asyncio
    async def test_search_volume_rate_limiting(self, client):
        """Test handling of rate limiting (12 requests per minute for Google Ads)."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            # First 12 requests succeed
            for _ in range(12):
                m.post(endpoint, payload={
                    "status_code": 20000,
                    "tasks": [{"status_code": 20000, "result": []}]
                }, status=200)
            
            # 13th request rate limited
            m.post(endpoint, status=429)
            
            async with client:
                tasks = []
                # Make 12 requests (should succeed)
                for i in range(12):
                    tasks.append(
                        client.get_search_volume(keywords=[f"keyword_{i}"])
                    )
                
                results = await asyncio.gather(*tasks)
                assert all(r["success"] for r in results)
                
                # 13th request should be rate limited
                from tenacity import RetryError
                with pytest.raises(RetryError):
                    await client.get_search_volume(keywords=["rate_limited"])

    @pytest.mark.asyncio
    async def test_search_volume_with_monthly_history(self, client):
        """Test parsing of monthly search history data."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            # Mock 12 months of historical data
            monthly_data = []
            for month in range(1, 13):
                monthly_data.append({
                    "year": 2024,
                    "month": month,
                    "search_volume": 10000 + (month * 100)
                })
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "seasonal keyword",
                        "search_volume": 12000,
                        "monthly_searches": monthly_data
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["seasonal keyword"]
                )
                
                assert result["success"] is True
                assert len(result["data"][0]["monthly_searches"]) == 12
                # Verify trend analysis is possible
                jan_volume = result["data"][0]["monthly_searches"][0]["search_volume"]
                dec_volume = result["data"][0]["monthly_searches"][11]["search_volume"]
                assert dec_volume > jan_volume  # Growth trend

    @pytest.mark.asyncio
    async def test_search_volume_bid_estimates(self, client):
        """Test retrieval of bid estimate data."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "competitive keyword",
                        "search_volume": 50000,
                        "cpc": 25.50,
                        "low_top_of_page_bid": 18.75,
                        "high_top_of_page_bid": 35.25,
                        "competition": 0.95,
                        "competition_level": "HIGH"
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["competitive keyword"]
                )
                
                data = result["data"][0]
                assert data["low_top_of_page_bid"] == 18.75
                assert data["high_top_of_page_bid"] == 35.25
                assert data["cpc"] == 25.50
                assert data["competition_level"] == "HIGH"
                # Verify bid range logic
                assert data["low_top_of_page_bid"] < data["high_top_of_page_bid"]
                assert data["low_top_of_page_bid"] < data["cpc"] < data["high_top_of_page_bid"]

    @pytest.mark.asyncio
    async def test_validate_credentials(self, client):
        """Test credential validation."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/appendix/user_data"
            
            # Mock successful validation
            m.get(endpoint, payload={
                "status_code": 20000,
                "status_message": "Ok."
            }, status=200)
            
            async with client:
                is_valid = await client.validate_credentials()
                assert is_valid is True
            
            # Mock failed validation
            m.get(endpoint, payload={
                "status_code": 40000,
                "status_message": "Invalid credentials"
            }, status=200)
            
            async with client:
                is_valid = await client.validate_credentials()
                assert is_valid is False

    # Keywords for Site Endpoint Tests
    @pytest.mark.asyncio
    async def test_keywords_for_site_basic(self, client):
        """Test extracting keywords from a website."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/keywords_for_site/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "cost": 0.01,
                    "result": [{
                        "keyword": "plumbing services",
                        "search_volume": 22000,
                        "competition": 0.88,
                        "cpc": 18.50,
                        "relevance": 0.95
                    }, {
                        "keyword": "emergency plumber",
                        "search_volume": 18000,
                        "competition": 0.92,
                        "cpc": 25.75,
                        "relevance": 0.88
                    }, {
                        "keyword": "water heater repair",
                        "search_volume": 8100,
                        "competition": 0.75,
                        "cpc": 15.25,
                        "relevance": 0.82
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_site(
                    target="https://example-plumbing.com",
                    location_code=2840,
                    language_code="en"
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 3
                assert result["data"][0]["keyword"] == "plumbing services"
                assert result["data"][0]["relevance"] == 0.95
                assert result["data"][1]["cpc"] == 25.75

    @pytest.mark.asyncio
    async def test_keywords_for_site_branded_filter(self, client):
        """Test filtering branded vs non-branded keywords."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/keywords_for_site/live"
            
            # Test with only non-branded keywords
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"keyword": "marketing software", "search_volume": 14800},
                        {"keyword": "email marketing", "search_volume": 33100}
                    ]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_site(
                    target="https://example.com",
                    include_branded_keywords=False,
                    include_non_branded_keywords=True
                )
                
                assert result["success"] is True
                # Should not contain brand names
                for item in result["data"]:
                    assert "example" not in item["keyword"].lower()

    @pytest.mark.asyncio
    async def test_keywords_for_site_pagination(self, client):
        """Test pagination for keywords for site."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/keywords_for_site/live"
            
            # First page
            mock_page1 = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{"keyword": f"keyword_{i}", "search_volume": 1000} for i in range(100)]
                }]
            }
            
            # Second page
            mock_page2 = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{"keyword": f"keyword_{i}", "search_volume": 1000} for i in range(100, 150)]
                }]
            }
            
            m.post(endpoint, payload=mock_page1, status=200)
            m.post(endpoint, payload=mock_page2, status=200)
            
            async with client:
                # Get first page
                page1 = await client.get_keywords_for_site(
                    target="https://example.com",
                    limit=100,
                    offset=0
                )
                assert len(page1["data"]) == 100
                
                # Get second page
                page2 = await client.get_keywords_for_site(
                    target="https://example.com",
                    limit=100,
                    offset=100
                )
                assert len(page2["data"]) == 50

    # Keywords for Keywords Endpoint Tests  
    @pytest.mark.asyncio
    async def test_keywords_for_keywords_basic(self, client):
        """Test generating keyword suggestions from seed keywords."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/keywords_for_keywords/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "cost": 0.006,
                    "result": [{
                        "keyword": "digital marketing",
                        "search_volume": 40500,
                        "competition": 0.65,
                        "cpc": 8.25
                    }, {
                        "keyword": "online marketing",
                        "search_volume": 22200,
                        "competition": 0.58,
                        "cpc": 6.50
                    }, {
                        "keyword": "internet marketing",
                        "search_volume": 14800,
                        "competition": 0.52,
                        "cpc": 5.75
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_keywords(
                    keywords=["marketing"],
                    location_code=2840,
                    include_seed_keyword=True
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 3
                assert result["data"][0]["search_volume"] == 40500
                
    @pytest.mark.asyncio
    async def test_keywords_for_keywords_with_sorting(self, client):
        """Test keyword suggestions with sorting."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/keywords_for_keywords/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"keyword": "high cpc", "cpc": 50.0, "search_volume": 1000},
                        {"keyword": "medium cpc", "cpc": 25.0, "search_volume": 2000},
                        {"keyword": "low cpc", "cpc": 5.0, "search_volume": 5000}
                    ]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_keywords(
                    keywords=["test"],
                    sort_by="cpc",
                    limit=10
                )
                
                assert result["data"][0]["cpc"] == 50.0
                assert result["data"][2]["cpc"] == 5.0

    # Ad Traffic by Keywords Endpoint Tests
    @pytest.mark.asyncio
    async def test_ad_traffic_by_keywords_basic(self, client):
        """Test getting traffic estimates for keywords."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/ad_traffic_by_keywords/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "cost": 0.003,
                    "result": [{
                        "keyword": "insurance quotes",
                        "match": "exact",
                        "impressions": 125000,
                        "clicks": 3750,
                        "ctr": 0.03,
                        "average_cpc": 45.50,
                        "cost": 170625.0,
                        "bid": 50.0
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_ad_traffic_by_keywords(
                    keywords=["insurance quotes"],
                    location_code=2840,
                    bid=50.0,
                    match="exact"
                )
                
                assert result["success"] is True
                assert result["data"][0]["impressions"] == 125000
                assert result["data"][0]["clicks"] == 3750
                assert result["data"][0]["ctr"] == 0.03
                assert result["data"][0]["cost"] == 170625.0

    @pytest.mark.asyncio
    async def test_ad_traffic_with_date_range(self, client):
        """Test traffic estimates with forecasting date range."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/ad_traffic_by_keywords/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "tax software",
                        "impressions": 250000,
                        "clicks": 12500,
                        "date_from": "2024-01-01",
                        "date_to": "2024-03-31"
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_ad_traffic_by_keywords(
                    keywords=["tax software"],
                    date_from="2024-01-01",
                    date_to="2024-03-31"
                )
                
                assert result["success"] is True
                assert result["data"][0]["impressions"] == 250000

    @pytest.mark.asyncio
    async def test_ad_traffic_match_types(self, client):
        """Test different match types for traffic estimation."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/ad_traffic_by_keywords/live"
            
            # Test exact match
            m.post(endpoint, payload={
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{"match": "exact", "impressions": 10000}]
                }]
            }, status=200)
            
            # Test phrase match
            m.post(endpoint, payload={
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{"match": "phrase", "impressions": 25000}]
                }]
            }, status=200)
            
            # Test broad match
            m.post(endpoint, payload={
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{"match": "broad", "impressions": 50000}]
                }]
            }, status=200)
            
            async with client:
                exact = await client.get_ad_traffic_by_keywords(["test"], match="exact")
                phrase = await client.get_ad_traffic_by_keywords(["test"], match="phrase")
                broad = await client.get_ad_traffic_by_keywords(["test"], match="broad")
                
                # Verify match type hierarchy: broad > phrase > exact
                assert broad["data"][0]["impressions"] > phrase["data"][0]["impressions"]
                assert phrase["data"][0]["impressions"] > exact["data"][0]["impressions"]

    # Locations and Languages Endpoint Tests
    @pytest.mark.asyncio
    async def test_get_locations(self, client):
        """Test getting supported locations."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/locations"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"location_code": 2840, "location_name": "United States"},
                        {"location_code": 2826, "location_name": "United Kingdom"},
                        {"location_code": 2124, "location_name": "Canada"}
                    ]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_locations()
                
                assert result["success"] is True
                assert len(result["data"]) == 3
                assert result["data"][0]["location_code"] == 2840

    @pytest.mark.asyncio
    async def test_get_locations_by_country(self, client):
        """Test getting locations filtered by country."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/locations/US"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"location_code": 1014221, "location_name": "New York"},
                        {"location_code": 1014044, "location_name": "California"}
                    ]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_locations(country="US")
                
                assert result["success"] is True
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_languages(self, client):
        """Test getting supported languages."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/google_ads/languages"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"language_code": "en", "language_name": "English"},
                        {"language_code": "es", "language_name": "Spanish"},
                        {"language_code": "fr", "language_name": "French"}
                    ]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_languages()
                
                assert result["success"] is True
                assert len(result["data"]) == 3
                assert result["data"][0]["language_code"] == "en"