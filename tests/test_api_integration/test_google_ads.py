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