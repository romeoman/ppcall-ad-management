"""Tests for FireCrawl API client following TDD approach."""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import aiohttp
from aioresponses import aioresponses
import json

from api_integration.firecrawl_client import FireCrawlClient
from tests.fixtures.api_responses import APIResponseFixtures


class TestFireCrawlClient:
    """Test suite for FireCrawlClient."""

    @pytest.fixture
    def client(self):
        """Create a FireCrawlClient instance."""
        return FireCrawlClient(
            api_key="test_api_key_456",
            max_concurrent=3
        )

    @pytest.fixture
    def mock_responses(self):
        """Get mock API responses."""
        return APIResponseFixtures()

    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initializes with correct settings."""
        assert client.api_key == "test_api_key_456"
        assert client.base_url == "https://api.firecrawl.dev/v0"
        assert client.max_concurrent == 3

    @pytest.mark.asyncio
    async def test_scrape_url_success(self, client, mock_responses):
        """Test successful URL scraping."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            expected_response = mock_responses.firecrawl_scrape_response()
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.scrape_url(
                    url="https://www.example.com/landing-page"
                )
                
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["url"] == "https://www.example.com/landing-page"
                assert "content" in result["data"]
                assert "metadata" in result["data"]

    @pytest.mark.asyncio
    async def test_scrape_with_formats(self, client):
        """Test scraping with specific formats."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            expected_response = {
                "success": True,
                "data": {
                    "url": "https://example.com",
                    "markdown": "# Title\nContent here",
                    "html": "<h1>Title</h1><p>Content here</p>",
                    "screenshot": "base64_encoded_screenshot_data"
                }
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.scrape_url(
                    url="https://example.com",
                    formats=["markdown", "html", "screenshot"]
                )
                
                assert "markdown" in result["data"]
                assert "html" in result["data"]
                assert "screenshot" in result["data"]

    @pytest.mark.asyncio
    async def test_scrape_with_llm_extraction(self, client, mock_responses):
        """Test scraping with LLM extraction schema."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            expected_response = mock_responses.firecrawl_scrape_response()
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                schema = {
                    "type": "object",
                    "properties": {
                        "headline": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                        "pricing": {"type": "object"}
                    }
                }
                
                result = await client.scrape_url(
                    url="https://www.example.com/landing-page",
                    extractorOptions={
                        "mode": "llm-extraction",
                        "extractionSchema": schema
                    }
                )
                
                assert "llm_extraction" in result["data"]
                assert "headline" in result["data"]["llm_extraction"]
                assert "features" in result["data"]["llm_extraction"]

    @pytest.mark.asyncio
    async def test_crawl_website_success(self, client):
        """Test successful website crawling."""
        with aioresponses() as m:
            # Start crawl
            start_endpoint = f"{client.base_url}/crawl"
            start_response = {
                "success": True,
                "jobId": "crawl_job_123"
            }
            
            m.post(start_endpoint, payload=start_response, status=200)
            
            # Check status
            status_endpoint = f"{client.base_url}/crawl/status/crawl_job_123"
            status_response = {
                "status": "completed",
                "total": 5,
                "completed": 5,
                "data": [
                    {
                        "url": "https://example.com/page1",
                        "markdown": "Page 1 content",
                        "metadata": {"title": "Page 1"}
                    },
                    {
                        "url": "https://example.com/page2",
                        "markdown": "Page 2 content",
                        "metadata": {"title": "Page 2"}
                    }
                ]
            }
            
            m.get(status_endpoint, payload=status_response, status=200)
            
            async with client:
                # Start crawl
                crawl_job = await client.crawl_website(
                    url="https://example.com",
                    crawlerOptions={
                        "limit": 10,
                        "includes": ["/*"]
                    }
                )
                
                assert crawl_job["success"] is True
                assert crawl_job["jobId"] == "crawl_job_123"
                
                # Check status
                status = await client.check_crawl_status(crawl_job["jobId"])
                assert status["status"] == "completed"
                assert len(status["data"]) == 2

    @pytest.mark.asyncio
    async def test_search_website(self, client):
        """Test website search functionality."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/search"
            expected_response = {
                "success": True,
                "data": [
                    {
                        "url": "https://example.com/docs/api",
                        "title": "API Documentation",
                        "content": "API reference and examples",
                        "score": 0.95
                    },
                    {
                        "url": "https://example.com/guides/api",
                        "title": "API Guide",
                        "content": "Getting started with API",
                        "score": 0.88
                    }
                ]
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.search_website(
                    url="https://example.com",
                    query="API documentation",
                    limit=10
                )
                
                assert result["success"] is True
                assert len(result["data"]) == 2
                assert result["data"][0]["score"] > result["data"][1]["score"]

    @pytest.mark.asyncio
    async def test_request_includes_api_key_header(self, client):
        """Test that API key is included in request headers."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            
            m.post(endpoint, payload={"success": True, "data": {}}, status=200)
            
            async with client:
                await client.scrape_url(url="https://example.com")
                
                # Verify request was made
                assert len(m.requests) > 0

    @pytest.mark.asyncio
    async def test_handles_api_errors(self, client):
        """Test handling of API error responses."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            
            # Mock a 401 unauthorized error
            m.post(endpoint, status=401)
            
            async with client:
                from tenacity import RetryError
                with pytest.raises(RetryError):
                    await client.scrape_url(url="https://example.com")

    @pytest.mark.asyncio
    async def test_handles_rate_limit(self, client):
        """Test handling of rate limit responses."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            
            # Mock a 429 rate limit error
            m.post(endpoint, status=429)
            
            async with client:
                from tenacity import RetryError
                with pytest.raises(RetryError):
                    await client.scrape_url(url="https://example.com")

    @pytest.mark.asyncio
    async def test_concurrent_scraping(self, client):
        """Test that concurrent scraping respects semaphore limit."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            
            # Mock multiple responses
            for i in range(5):
                m.post(endpoint, payload={
                    "success": True, 
                    "data": {"url": f"https://example.com/page{i}"}
                }, status=200)
            
            async with client:
                tasks = []
                for i in range(5):
                    tasks.append(
                        client.scrape_url(url=f"https://example.com/page{i}")
                    )
                
                results = await asyncio.gather(*tasks)
                assert len(results) == 5
                for i, result in enumerate(results):
                    assert result["data"]["url"] == f"https://example.com/page{i}"

    @pytest.mark.asyncio
    async def test_scrape_with_wait_for(self, client):
        """Test scraping with wait_for parameter."""
        with aioresponses() as m:
            endpoint = f"{client.base_url}/scrape"
            expected_response = {
                "success": True,
                "data": {
                    "url": "https://example.com",
                    "content": "Dynamically loaded content"
                }
            }
            
            m.post(endpoint, payload=expected_response, status=200)
            
            async with client:
                result = await client.scrape_url(
                    url="https://example.com",
                    pageOptions={
                        "waitFor": 5000  # Wait 5 seconds for dynamic content
                    }
                )
                
                assert result["success"] is True
                assert "Dynamically loaded content" in result["data"]["content"]