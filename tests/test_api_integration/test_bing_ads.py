"""Tests for Bing Ads DataForSEO client following TDD approach."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from aioresponses import aioresponses
import json
from datetime import datetime

from api_integration.dataforseo.bing_ads_client import BingAdsClient
from tests.fixtures.api_responses import APIResponseFixtures


class TestBingAdsClient:
    """Test suite for BingAdsClient."""

    @pytest.fixture
    def client(self):
        """Create a BingAdsClient instance."""
        return BingAdsClient(
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

    # Search Volume Endpoint Tests
    @pytest.mark.asyncio
    async def test_bing_search_volume(self, client):
        """Test getting search volume for Bing keywords."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/search_volume/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "cost": 0.004,
                    "result": [{
                        "keyword": "office software",
                        "search_volume": 8900,
                        "competition": 0.72,
                        "cpc": 12.30,
                        "device_info": {
                            "desktop": 5500,
                            "mobile": 2800,
                            "tablet": 600
                        }
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume(
                    keywords=["office software"],
                    location_code=2840,
                    device="desktop"
                )
                
                assert result["success"] is True
                assert result["data"][0]["search_volume"] == 8900
                assert result["data"][0]["device_info"]["desktop"] == 5500

    @pytest.mark.asyncio
    async def test_bing_search_volume_history(self, client):
        """Test getting historical search volume for Bing."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/search_volume_history/live"
            
            # Mock 12 months of data
            monthly_data = [
                {"year": 2024, "month": i, "search_volume": 5000 + i * 100}
                for i in range(1, 13)
            ]
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "cloud storage",
                        "monthly_searches": monthly_data
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_search_volume_history(
                    keywords=["cloud storage"],
                    date_from="2024-01-01",
                    date_to="2024-12-31"
                )
                
                assert result["success"] is True
                assert len(result["data"][0]["monthly_searches"]) == 12

    # Keywords for Site Tests
    @pytest.mark.asyncio
    async def test_bing_keywords_for_site(self, client):
        """Test extracting keywords for a site on Bing."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/keywords_for_site/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "project management",
                        "search_volume": 15000,
                        "competition": 0.65
                    }, {
                        "keyword": "task tracking",
                        "search_volume": 8200,
                        "competition": 0.55
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_site(
                    target="https://example.com",
                    location_code=2840
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 2
                assert result["data"][0]["keyword"] == "project management"

    # Keywords for Keywords Tests
    @pytest.mark.asyncio
    async def test_bing_keywords_for_keywords(self, client):
        """Test generating keyword suggestions on Bing."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/keywords_for_keywords/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "email marketing",
                        "search_volume": 22000,
                        "competition": 0.58
                    }, {
                        "keyword": "email automation",
                        "search_volume": 12000,
                        "competition": 0.52
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keywords_for_keywords(
                    keywords=["email"],
                    include_seed_keyword=False
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 2

    # Keyword Performance Tests
    @pytest.mark.asyncio
    async def test_bing_keyword_performance(self, client):
        """Test device-specific performance metrics."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/keyword_performance/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "mobile apps",
                        "device_performance": {
                            "desktop": {
                                "ctr": 0.025,
                                "impressions": 50000,
                                "clicks": 1250,
                                "position": 2.3
                            },
                            "mobile": {
                                "ctr": 0.038,
                                "impressions": 80000,
                                "clicks": 3040,
                                "position": 1.8
                            },
                            "tablet": {
                                "ctr": 0.020,
                                "impressions": 15000,
                                "clicks": 300,
                                "position": 2.5
                            }
                        }
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keyword_performance(
                    keywords=["mobile apps"],
                    match="exact"
                )
                
                assert result["success"] is True
                perf = result["data"][0]["device_performance"]
                assert perf["mobile"]["ctr"] > perf["desktop"]["ctr"]
                assert perf["mobile"]["position"] < perf["desktop"]["position"]

    # Keyword Suggestions for URL Tests
    @pytest.mark.asyncio
    async def test_bing_keyword_suggestions_for_url(self, client):
        """Test AI-powered keyword suggestions from URL."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/keyword_suggestions_for_url/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "keyword": "plumbing repair",
                        "confidence_score": 0.92,
                        "relevance": "high"
                    }, {
                        "keyword": "emergency plumber",
                        "confidence_score": 0.88,
                        "relevance": "high"
                    }, {
                        "keyword": "water heater installation",
                        "confidence_score": 0.85,
                        "relevance": "medium"
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_keyword_suggestions_for_url(
                    target="https://plumbingservice.com",
                    exclude_brands=True
                )
                
                assert result["success"] is True
                assert result["data"][0]["confidence_score"] == 0.92
                assert result["data"][0]["relevance"] == "high"

    # Audience Estimation Tests
    @pytest.mark.asyncio
    async def test_bing_audience_estimation(self, client):
        """Test audience size and demographics estimation."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/audience_estimation/live"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "audience_size": 2500000,
                        "demographics": {
                            "age_groups": {
                                "18-24": 0.15,
                                "25-34": 0.28,
                                "35-44": 0.25,
                                "45-54": 0.18,
                                "55+": 0.14
                            },
                            "gender": {
                                "male": 0.52,
                                "female": 0.48
                            }
                        },
                        "geographic_distribution": {
                            "United States": 0.65,
                            "Canada": 0.15,
                            "United Kingdom": 0.12,
                            "Other": 0.08
                        },
                        "device_usage": {
                            "desktop": 0.45,
                            "mobile": 0.40,
                            "tablet": 0.15
                        },
                        "estimated_reach": {
                            "daily": 85000,
                            "weekly": 450000,
                            "monthly": 1500000
                        }
                    }]
                }]
            }
            
            m.post(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_audience_estimation(
                    keywords=["insurance", "quotes"],
                    location_code=2840,
                    bid=25.0,
                    daily_budget=500.0
                )
                
                assert result["success"] is True
                data = result["data"][0]
                assert data["audience_size"] == 2500000
                assert data["demographics"]["age_groups"]["25-34"] == 0.28
                assert data["device_usage"]["desktop"] == 0.45
                assert data["estimated_reach"]["daily"] == 85000

    # Overview Endpoint Test
    @pytest.mark.asyncio
    async def test_bing_overview(self, client):
        """Test getting Bing Ads API overview."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/overview"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "api_version": "v3",
                        "endpoints_available": 10,
                        "rate_limits": {
                            "requests_per_minute": 20,
                            "requests_per_day": 10000
                        },
                        "features": [
                            "search_volume",
                            "keyword_performance",
                            "audience_estimation"
                        ]
                    }]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_overview()
                
                assert result["success"] is True
                assert result["data"][0]["endpoints_available"] == 10

    # Locations Test
    @pytest.mark.asyncio
    async def test_bing_locations(self, client):
        """Test getting Bing supported locations."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/locations"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"location_code": 2840, "location_name": "United States"},
                        {"location_code": 2124, "location_name": "Canada"}
                    ]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_locations()
                
                assert result["success"] is True
                assert len(result["data"]) == 2

    # Languages Test
    @pytest.mark.asyncio
    async def test_bing_languages(self, client):
        """Test getting Bing supported languages."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/languages"
            
            mock_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [
                        {"language_code": "en", "language_name": "English"},
                        {"language_code": "fr", "language_name": "French"}
                    ]
                }]
            }
            
            m.get(endpoint, payload=mock_response, status=200)
            
            async with client:
                result = await client.get_languages()
                
                assert result["success"] is True
                assert result["data"][0]["language_code"] == "en"

    # Test match types for Bing
    @pytest.mark.asyncio
    async def test_bing_match_types_performance(self, client):
        """Test different match types impact on performance."""
        with aioresponses() as m:
            endpoint = f"{client.BASE_URL}/keywords_data/bing/keyword_performance/live"
            
            # Mock responses for different match types
            exact_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "match": "exact",
                        "impressions": 10000,
                        "ctr": 0.04
                    }]
                }]
            }
            
            phrase_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "match": "phrase",
                        "impressions": 25000,
                        "ctr": 0.025
                    }]
                }]
            }
            
            broad_response = {
                "status_code": 20000,
                "tasks": [{
                    "status_code": 20000,
                    "result": [{
                        "match": "broad",
                        "impressions": 50000,
                        "ctr": 0.015
                    }]
                }]
            }
            
            m.post(endpoint, payload=exact_response, status=200)
            m.post(endpoint, payload=phrase_response, status=200)
            m.post(endpoint, payload=broad_response, status=200)
            
            async with client:
                exact = await client.get_keyword_performance(["test"], match="exact")
                phrase = await client.get_keyword_performance(["test"], match="phrase")
                broad = await client.get_keyword_performance(["test"], match="broad")
                
                # Verify match type patterns
                assert broad["data"][0]["impressions"] > phrase["data"][0]["impressions"]
                assert phrase["data"][0]["impressions"] > exact["data"][0]["impressions"]
                assert exact["data"][0]["ctr"] > phrase["data"][0]["ctr"]
                assert phrase["data"][0]["ctr"] > broad["data"][0]["ctr"]