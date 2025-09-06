"""Tests for the landing page scraper module."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from bs4 import BeautifulSoup

from src.processors.landing_page_scraper import LandingPageScraper
from models.competition_models import ScrapedCopy
from api_integration.firecrawl_client import FireCrawlClient


@pytest.fixture
def mock_firecrawl_client():
    """Create a mock FireCrawl client."""
    client = Mock(spec=FireCrawlClient)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    client.scrape_url = AsyncMock()
    return client


@pytest.fixture
def landing_page_scraper(mock_firecrawl_client):
    """Create a landing page scraper instance."""
    return LandingPageScraper(firecrawl_client=mock_firecrawl_client)


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
    <head>
        <title>Best Plumbing Services | Quick & Reliable</title>
        <meta name="description" content="Professional plumbing services available 24/7">
    </head>
    <body>
        <header>
            <h1>Emergency Plumbing Services - Available 24/7</h1>
            <h2>Fast, Reliable, and Affordable Solutions</h2>
        </header>
        <main>
            <p>We provide top-quality plumbing services for residential and commercial properties. 
               Our experienced technicians are available around the clock to handle any plumbing emergency.</p>
            <p>With over 20 years of experience, we guarantee satisfaction and competitive pricing.</p>
            
            <div class="pricing">
                <h3>Our Pricing</h3>
                <p>Service calls starting at $89. Emergency services from $149.</p>
            </div>
            
            <ul class="features">
                <li>24/7 Emergency Service</li>
                <li>Licensed and Insured Technicians</li>
                <li>Same Day Service Available</li>
                <li>Free Estimates</li>
                <li>100% Satisfaction Guarantee</li>
            </ul>
            
            <div class="cta-section">
                <button class="btn-primary">Get Free Quote</button>
                <a href="/schedule" class="button">Schedule Service</a>
                <input type="submit" value="Contact Us Now">
            </div>
            
            <section class="testimonials">
                <blockquote>"Best plumbing service in town! Quick response and fair pricing."</blockquote>
                <div class="review">"They fixed our leak in under an hour. Highly recommended!"</div>
            </section>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """
# Professional Plumbing Services

## Your Trusted Local Plumbers

We offer comprehensive plumbing solutions for all your needs.

### Our Services Include:
- Emergency repairs
- Drain cleaning
- Water heater installation
- Leak detection

Contact us today for a [Free Estimate](https://example.com/estimate) or 
[Schedule Service Now](https://example.com/schedule).

Starting at just $99 per service call.
"""


@pytest.fixture
def firecrawl_response_html(sample_html):
    """Mock FireCrawl API response with HTML."""
    return {
        'data': {
            'html': sample_html,
            'markdown': '',
            'metadata': {
                'title': 'Best Plumbing Services | Quick & Reliable',
                'description': 'Professional plumbing services available 24/7'
            }
        }
    }


@pytest.fixture
def firecrawl_response_markdown(sample_markdown):
    """Mock FireCrawl API response with markdown."""
    return {
        'data': {
            'html': '',
            'markdown': sample_markdown,
            'metadata': {
                'title': 'Professional Plumbing Services',
                'description': 'Comprehensive plumbing solutions'
            }
        }
    }


class TestLandingPageScraper:
    """Tests for the LandingPageScraper class."""
    
    @pytest.mark.asyncio
    async def test_scrape_landing_pages_success(self, landing_page_scraper, mock_firecrawl_client, firecrawl_response_html):
        """Test successful scraping of landing pages."""
        urls = ['https://example.com', 'https://test.com']
        mock_firecrawl_client.scrape_url.return_value = firecrawl_response_html
        
        results = await landing_page_scraper.scrape_landing_pages(urls)
        
        assert len(results) == 2
        assert all(isinstance(r, ScrapedCopy) for r in results)
        assert all(r.scrape_success for r in results)
        assert mock_firecrawl_client.scrape_url.call_count == 2
    
    @pytest.mark.asyncio
    async def test_scrape_landing_pages_with_error(self, landing_page_scraper, mock_firecrawl_client):
        """Test scraping with error handling."""
        urls = ['https://example.com', 'https://error.com']
        
        # First URL succeeds, second fails
        mock_firecrawl_client.scrape_url.side_effect = [
            {'data': {'html': '<h1>Success</h1>', 'markdown': '', 'metadata': {}}},
            Exception('Connection timeout')
        ]
        
        results = await landing_page_scraper.scrape_landing_pages(urls)
        
        assert len(results) == 2
        assert results[0].scrape_success is True
        assert results[1].scrape_success is False
        assert 'Connection timeout' in results[1].error_message
    
    @pytest.mark.asyncio
    async def test_scrape_without_client(self):
        """Test scraping without FireCrawl client."""
        scraper = LandingPageScraper()  # No client provided
        results = await scraper.scrape_landing_pages(['https://example.com'])
        
        assert results == []
    
    def test_extract_copy_from_html(self, landing_page_scraper, firecrawl_response_html):
        """Test extracting copy from HTML content."""
        scraped = landing_page_scraper._extract_copy('https://example.com', firecrawl_response_html)
        
        assert scraped.url == 'https://example.com'
        assert scraped.headline == 'Emergency Plumbing Services - Available 24/7'
        assert scraped.subheadline == 'Fast, Reliable, and Affordable Solutions'
        assert scraped.cta == 'Get Free Quote'
        assert 'Schedule Service' in scraped.secondary_ctas
        assert 'Contact Us Now' in scraped.secondary_ctas
        assert 'top-quality plumbing services' in scraped.body_snippet
        assert scraped.pricing and '$89' in scraped.pricing
        assert len(scraped.features) == 5
        assert '24/7 Emergency Service' in scraped.features
        assert len(scraped.testimonials) > 0
        assert scraped.meta_title == 'Best Plumbing Services | Quick & Reliable'
        assert scraped.scrape_success is True
    
    def test_extract_copy_from_markdown(self, landing_page_scraper, firecrawl_response_markdown):
        """Test extracting copy from markdown content."""
        scraped = landing_page_scraper._extract_copy('https://example.com', firecrawl_response_markdown)
        
        assert scraped.headline == 'Professional Plumbing Services'
        assert scraped.subheadline == 'Your Trusted Local Plumbers'
        assert scraped.cta == 'Free Estimate'
        assert 'Schedule Service Now' in scraped.secondary_ctas
        assert 'comprehensive plumbing solutions' in scraped.body_snippet
        assert scraped.scrape_success is True
    
    def test_extract_copy_with_error(self, landing_page_scraper):
        """Test extract_copy with malformed data."""
        bad_response = {'data': None}
        scraped = landing_page_scraper._extract_copy('https://example.com', bad_response)
        
        assert scraped.url == 'https://example.com'
        assert scraped.scrape_success is False
        assert scraped.error_message is not None
    
    def test_clean_text(self, landing_page_scraper):
        """Test text cleaning functionality."""
        dirty_text = "  Too   much   whitespace  &nbsp; &amp;  "
        clean = landing_page_scraper._clean_text(dirty_text)
        assert clean == "Too much whitespace"
        
        assert landing_page_scraper._clean_text(None) == ""
        assert landing_page_scraper._clean_text("") == ""
    
    def test_extract_ctas(self, landing_page_scraper, sample_html):
        """Test CTA extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        ctas = landing_page_scraper._extract_ctas(soup)
        
        assert len(ctas) == 3
        assert 'Get Free Quote' in ctas
        assert 'Schedule Service' in ctas
        assert 'Contact Us Now' in ctas
    
    def test_extract_body_text(self, landing_page_scraper, sample_html):
        """Test body text extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        body_text = landing_page_scraper._extract_body_text(soup)
        
        assert 'top-quality plumbing services' in body_text
        assert 'experienced technicians' in body_text
        assert len(body_text) <= 1000
    
    def test_extract_features(self, landing_page_scraper, sample_html):
        """Test feature extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        features = landing_page_scraper._extract_features(soup)
        
        assert len(features) == 5
        assert '24/7 Emergency Service' in features
        assert 'Free Estimates' in features
    
    def test_extract_pricing(self, landing_page_scraper, sample_html):
        """Test pricing extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        pricing = landing_page_scraper._extract_pricing(soup)
        
        assert pricing is not None
        assert '$89' in pricing
        # Pricing now returns multiple price mentions separated by |
        assert 'starting at' in pricing.lower() or 'from' in pricing.lower()
    
    def test_extract_testimonials(self, landing_page_scraper, sample_html):
        """Test testimonial extraction."""
        soup = BeautifulSoup(sample_html, 'html.parser')
        testimonials = landing_page_scraper._extract_testimonials(soup)
        
        assert len(testimonials) > 0
        assert any('Best plumbing service' in t for t in testimonials)
    
    def test_analyze_copy_trends(self, landing_page_scraper):
        """Test trend analysis across multiple scraped pages."""
        scraped_data = [
            ScrapedCopy(
                url='https://example1.com',
                headline='Emergency Plumbing Services',
                cta='Get Quote',
                secondary_ctas=['Call Now', 'Book Online'],
                body_snippet='Professional plumbing services available 24/7',
                features=['24/7 Service', 'Licensed', 'Insured'],
                pricing='Starting at $99',
                scrape_success=True
            ),
            ScrapedCopy(
                url='https://example2.com',
                headline='Professional Plumbing Solutions',
                cta='Get Quote',
                secondary_ctas=['Schedule Now'],
                body_snippet='Expert plumbing repairs and installation',
                features=['Emergency Service', 'Free Estimates', 'Licensed'],
                pricing='From $89 per hour',
                scrape_success=True
            ),
            ScrapedCopy(
                url='https://example3.com',
                scrape_success=False,
                error_message='Timeout'
            )
        ]
        
        analysis = landing_page_scraper.analyze_copy_trends(scraped_data)
        
        assert analysis['total_pages'] == 3
        assert analysis['successful_scrapes'] == 2
        assert len(analysis['common_headline_words']) > 0
        assert any('plumbing' in word for word, _ in analysis['common_headline_words'])
        assert ('Get Quote', 2) in analysis['common_ctas']
        assert 'average_word_counts' in analysis
        assert 'cta_patterns' in analysis
        assert 'pricing_patterns' in analysis
    
    def test_analyze_pricing_patterns(self, landing_page_scraper):
        """Test pricing pattern analysis."""
        pricing_list = [
            'Starting at $99 per month',
            'From $149 one-time fee',
            '$89 per user per month',
            '€75 monthly subscription'
        ]
        
        patterns = landing_page_scraper._analyze_pricing_patterns(pricing_list)
        
        assert len(patterns['price_points']) == 3  # USD prices only
        assert patterns['pricing_models']['monthly'] == 2
        assert patterns['pricing_models']['one_time'] == 1
        assert patterns['pricing_models']['per_user'] == 1
        assert patterns['currency']['USD'] == 3
        assert patterns['currency']['EUR'] == 1
        assert 'price_stats' in patterns
        assert patterns['price_stats']['min'] == 89
        assert patterns['price_stats']['max'] == 149
    
    def test_generate_copy_insights(self, landing_page_scraper):
        """Test insight generation from analysis."""
        analysis = {
            'total_pages': 5,
            'successful_scrapes': 4,
            'common_headline_words': [('plumbing', 10), ('emergency', 8), ('service', 7)],
            'common_ctas': [('Get Quote', 5), ('Call Now', 3)],
            'common_features': [('licensed', 6), ('insured', 5)],
            'pricing_patterns': {
                'price_stats': {'min': 50, 'max': 200, 'average': 125},
                'pricing_models': {'monthly': 3, 'yearly': 1}
            },
            'average_word_counts': {'headline': 5.2, 'body': 150.5},
            'cta_patterns': {'average_length': 2.5}
        }
        
        insights = landing_page_scraper.generate_copy_insights(analysis)
        
        assert len(insights) > 0
        assert any('headline keywords' in i for i in insights)
        assert any('CTAs' in i for i in insights)
        assert any('Price range' in i for i in insights)
        assert any('pricing model: monthly' in i for i in insights)
        assert any('success rate: 80.0%' in i for i in insights)
    
    def test_scraped_copy_model(self):
        """Test ScrapedCopy model functionality."""
        scraped = ScrapedCopy(
            url='example.com',  # Test URL normalization
            headline='Test Headline',
            body_snippet='This is a test body snippet with some content.',
            cta='Click Here'
        )
        
        assert scraped.url == 'https://example.com'
        assert scraped.domain == 'example.com'
        
        word_counts = scraped.get_word_count()
        assert word_counts['headline'] == 2
        assert word_counts['body'] == 9
        assert word_counts['cta'] == 2
        
        keywords = scraped.extract_keywords()
        assert 'test' in keywords
        assert 'headline' in keywords
        assert 'body' in keywords  # 'content' includes period so becomes 'content.'


@pytest.mark.asyncio
class TestAsyncIntegration:
    """Test async integration with FireCrawl."""
    
    async def test_batch_scraping(self, landing_page_scraper, mock_firecrawl_client):
        """Test batch scraping of multiple URLs."""
        urls = [f'https://example{i}.com' for i in range(5)]
        
        mock_firecrawl_client.scrape_url.return_value = {
            'data': {
                'html': '<h1>Test</h1><p>Content</p>',
                'markdown': '',
                'metadata': {}
            }
        }
        
        results = await landing_page_scraper.scrape_landing_pages(urls)
        
        assert len(results) == 5
        assert mock_firecrawl_client.scrape_url.call_count == 5
        assert all(r.scrape_success for r in results)