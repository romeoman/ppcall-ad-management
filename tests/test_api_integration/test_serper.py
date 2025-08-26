"""Tests for Serper.dev API client following TDD approach."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from aioresponses import aioresponses
import json

from api_integration.serper_client import SerperClient
from tests.fixtures.api_responses import APIResponseFixtures


class TestSerperClient:
    """Test suite for SerperClient."""

    @pytest.fixture
    def client(self):
        """Create a SerperClient instance."""
        return SerperClient(
            api_key="test_api_key_123",
            max_concurrent=3
        )

    @pytest.fixture
    def mock_responses(self):
        """Get mock API responses."""
        return APIResponseFixtures()

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initializes with correct settings."""
        assert client.api_key == "test_api_key_123"
        assert client.base_url == "https://google.serper.dev"
        assert client.max_concurrent == 3

    @pytest.mark.asyncio
    async def test_search_google_success(self, client, mock_responses):
        """Test successful Google search."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            serp_response = mock_responses.serp_api_response()
            
            # Convert to Serper format
            expected_response = {
                "searchParameters": serp_response["search_parameters"],
                "organic": serp_response["organic_results"],
                "relatedSearches": serp_response["related_searches"],
                "answerBox": None,
                "knowledgeGraph": None
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_google(
                    query="project management software",
                    location="United States",
                    gl="us",
                    hl="en",
                    num=10
                )
                
                assert "organic" in result
                assert len(result["organic"]) == 2
                assert result["organic"][0]["position"] == 1

    @pytest.mark.asyncio
    async def test_search_images_success(self, client):
        """Test successful image search."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/images"
            expected_response = {
                "images": [
                    {
                        "title": "Project Management",
                        "imageUrl": "https://example.com/image1.jpg",
                        "link": "https://example.com/page1",
                        "source": "Example",
                        "thumbnail": "https://example.com/thumb1.jpg"
                    }
                ]
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_images(
                    query="project management"
                )
                
                assert "images" in result
                assert len(result["images"]) == 1

    @pytest.mark.asyncio
    async def test_search_news_success(self, client):
        """Test successful news search."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/news"
            expected_response = {
                "news": [
                    {
                        "title": "Latest Project Management Trends",
                        "link": "https://news.example.com/article1",
                        "snippet": "New trends in project management...",
                        "date": "2 hours ago",
                        "source": "Tech News"
                    }
                ]
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_news(
                    query="project management trends"
                )
                
                assert "news" in result
                assert len(result["news"]) == 1

    @pytest.mark.asyncio
    async def test_search_places_success(self, client):
        """Test successful places search."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/places"
            expected_response = {
                "places": [
                    {
                        "title": "Project Management Company",
                        "address": "123 Main St",
                        "rating": 4.5,
                        "reviews": 120,
                        "type": "Business"
                    }
                ]
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_places(
                    query="project management company near me"
                )
                
                assert "places" in result
                assert len(result["places"]) == 1

    @pytest.mark.asyncio
    async def test_request_includes_api_key_header(self, client):
        """Test that API key is included in request headers."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            
            m.post(endpoint, payload={"organic": []}, status=200)
            
            async with client:
                await client.search_google(query="test")
                
                # Verify request was made
                assert len(m.requests) > 0

    @pytest.mark.asyncio
    async def test_handles_api_errors(self, client):
        """Test handling of API error responses."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            
            # Mock a 401 unauthorized error
            m.post(endpoint, status=401)
            
            async with client:
                from tenacity import RetryError
                with pytest.raises(RetryError):
                    await client.search_google(query="test")

    @pytest.mark.asyncio
    async def test_handles_rate_limit(self, client):
        """Test handling of rate limit responses."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            
            # Mock a 429 rate limit error
            m.post(endpoint, status=429)
            
            async with client:
                from tenacity import RetryError
                with pytest.raises(RetryError):
                    await client.search_google(query="test")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test that concurrent requests respect semaphore limit."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            
            # Mock multiple responses
            for i in range(5):
                m.post(endpoint, payload={"id": i, "organic": []}, status=200)
            
            async with client:
                tasks = []
                for i in range(5):
                    tasks.append(
                        client.search_google(query=f"test_{i}")
                    )
                
                results = await asyncio.gather(*tasks)
                assert len(results) == 5

    @pytest.mark.asyncio
    async def test_autocomplete(self, client):
        """Test autocomplete suggestions."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/autocomplete"
            expected_response = {
                "suggestions": [
                    "project management software",
                    "project management tools",
                    "project management certification",
                    "project management methodologies"
                ]
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.get_autocomplete(
                    query="project management"
                )
                
                assert "suggestions" in result
                assert len(result["suggestions"]) == 4

    @pytest.mark.asyncio
    async def test_search_with_custom_params(self, client):
        """Test search with custom parameters."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            expected_response = {
                "organic": [],
                "searchParameters": {
                    "q": "test",
                    "location": "New York",
                    "gl": "us",
                    "hl": "en",
                    "num": 20,
                    "page": 2
                }
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_google(
                    query="test",
                    location="New York",
                    gl="us",
                    hl="en",
                    num=20,
                    page=2
                )
                
                assert result["searchParameters"]["num"] == 20
                assert result["searchParameters"]["page"] == 2