"""FireCrawl API client for web scraping and crawling."""

import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from .base_client import BaseAPIClient


class FireCrawlClient(BaseAPIClient):
    """Client for FireCrawl API - web scraping to understand landing pages."""
    
    def __init__(self, api_key: str, max_concurrent: int = 5):
        """
        Initialize FireCrawl client.
        
        Args:
            api_key: FireCrawl API key
            max_concurrent: Maximum concurrent requests
        """
        super().__init__(max_concurrent)
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v0"
    
    async def __aenter__(self):
        """Create session with proper headers."""
        await super().__aenter__()
        if self.session:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        return self
    
    async def scrape_url(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        pageOptions: Optional[Dict[str, Any]] = None,
        extractorOptions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scrape a single URL to understand landing page content.
        
        Args:
            url: URL to scrape
            formats: Output formats (markdown, html, screenshot, etc.)
            pageOptions: Page loading options (waitFor, headers, etc.)
            extractorOptions: LLM extraction options
            **kwargs: Additional parameters
            
        Returns:
            Scraped content with metadata
        """
        endpoint = f"{self.base_url}/scrape"
        
        payload = {
            "url": url
        }
        
        if formats:
            payload["pageOptions"] = payload.get("pageOptions", {})
            payload["pageOptions"]["formats"] = formats
        
        if pageOptions:
            payload["pageOptions"] = {**payload.get("pageOptions", {}), **pageOptions}
            
        if extractorOptions:
            payload["extractorOptions"] = extractorOptions
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def crawl_website(
        self,
        url: str,
        crawlerOptions: Optional[Dict[str, Any]] = None,
        pageOptions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a crawl job to scrape multiple pages from a website.
        
        Args:
            url: Starting URL for crawl
            crawlerOptions: Crawl options (limit, includes, excludes, etc.)
            pageOptions: Page loading options
            **kwargs: Additional parameters
            
        Returns:
            Crawl job information including jobId
        """
        endpoint = f"{self.base_url}/crawl"
        
        payload = {
            "url": url
        }
        
        if crawlerOptions:
            payload["crawlerOptions"] = crawlerOptions
            
        if pageOptions:
            payload["pageOptions"] = pageOptions
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def check_crawl_status(
        self,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Check the status of a crawl job.
        
        Args:
            job_id: The job ID returned from crawl_website
            
        Returns:
            Crawl job status and results if completed
        """
        endpoint = f"{self.base_url}/crawl/status/{job_id}"
        
        return await self._make_request("GET", endpoint)
    
    async def search_website(
        self,
        url: str,
        query: str,
        limit: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search a website for specific content.
        
        Args:
            url: Website URL to search
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional parameters
            
        Returns:
            Search results with relevance scores
        """
        endpoint = f"{self.base_url}/search"
        
        payload = {
            "url": url,
            "query": query
        }
        
        if limit:
            payload["limit"] = limit
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def scrape_batch(
        self,
        urls: List[str],
        formats: Optional[List[str]] = None,
        pageOptions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs in batch.
        
        Args:
            urls: List of URLs to scrape
            formats: Output formats
            pageOptions: Page loading options
            **kwargs: Additional parameters
            
        Returns:
            List of scraped results
        """
        tasks = []
        for url in urls:
            tasks.append(
                self.scrape_url(
                    url=url,
                    formats=formats,
                    pageOptions=pageOptions,
                    **kwargs
                )
            )
        
        return await asyncio.gather(*tasks)
    
    async def extract_structured_data(
        self,
        url: str,
        schema: Dict[str, Any],
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a URL using LLM.
        
        Args:
            url: URL to scrape and extract from
            schema: JSON schema for extraction
            prompt: Optional prompt to guide extraction
            
        Returns:
            Extracted structured data
        """
        extractorOptions = {
            "mode": "llm-extraction",
            "extractionSchema": schema
        }
        
        if prompt:
            extractorOptions["extractionPrompt"] = prompt
        
        result = await self.scrape_url(
            url=url,
            extractorOptions=extractorOptions
        )
        
        return result.get("data", {}).get("llm_extraction", {})