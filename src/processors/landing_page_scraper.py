"""Landing page scraper for competitor analysis."""

import re
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from api_integration.firecrawl_client import FireCrawlClient
from models.competition_models import ScrapedCopy


logger = logging.getLogger(__name__)


class LandingPageScraper:
    """Scrapes and analyzes competitor landing pages."""
    
    def __init__(self, firecrawl_client: Optional[FireCrawlClient] = None):
        """
        Initialize the landing page scraper.
        
        Args:
            firecrawl_client: FireCrawl API client instance
        """
        self.firecrawl_client = firecrawl_client
        
    async def scrape_landing_pages(
        self,
        urls: List[str],
        formats: Optional[List[str]] = None
    ) -> List[ScrapedCopy]:
        """
        Scrape multiple landing pages using FireCrawl API.
        
        Args:
            urls: List of URLs to scrape
            formats: Output formats (default: ['html', 'markdown'])
            
        Returns:
            List of ScrapedCopy objects
        """
        if not self.firecrawl_client:
            logger.error("FireCrawl client not initialized")
            return []
        
        if not formats:
            formats = ['html', 'markdown']
        
        scraped_data = []
        
        async with self.firecrawl_client:
            for url in urls:
                try:
                    logger.info(f"Scraping URL: {url}")
                    
                    # Scrape using FireCrawl
                    result = await self.firecrawl_client.scrape_url(
                        url=url,
                        formats=formats,
                        pageOptions={
                            'waitFor': 3000,  # Wait for dynamic content
                            'screenshot': False
                        }
                    )
                    
                    # Extract copy from the scraped content
                    scraped_copy = self._extract_copy(url, result)
                    scraped_data.append(scraped_copy)
                    
                except Exception as e:
                    logger.error(f"Error scraping URL '{url}': {e}")
                    # Add failed record
                    scraped_data.append(ScrapedCopy(
                        url=url,
                        scrape_success=False,
                        error_message=str(e)
                    ))
        
        return scraped_data
    
    def _extract_copy(self, url: str, page_data: Dict[str, Any]) -> ScrapedCopy:
        """
        Extract relevant copy elements from scraped page data.
        
        Args:
            url: Original URL
            page_data: Response from FireCrawl API
            
        Returns:
            ScrapedCopy object with extracted content
        """
        scraped = ScrapedCopy(url=url)
        
        try:
            # Get HTML content from FireCrawl response
            html_content = page_data.get('data', {}).get('html', '')
            markdown_content = page_data.get('data', {}).get('markdown', '')
            metadata = page_data.get('data', {}).get('metadata', {})
            
            # Extract metadata
            scraped.meta_title = metadata.get('title', '')
            scraped.meta_description = metadata.get('description', '')
            
            if html_content:
                # Parse with BeautifulSoup for better extraction
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract headlines
                h1 = soup.find('h1')
                scraped.headline = self._clean_text(h1.get_text()) if h1 else None
                
                h2 = soup.find('h2')
                scraped.subheadline = self._clean_text(h2.get_text()) if h2 else None
                
                # Extract CTAs (buttons and submit inputs)
                ctas = self._extract_ctas(soup)
                if ctas:
                    scraped.cta = ctas[0]
                    scraped.secondary_ctas = ctas[1:5]  # Limit to 5 secondary CTAs
                
                # Extract body text
                scraped.body_snippet = self._extract_body_text(soup)
                
                # Extract features (often in lists)
                scraped.features = self._extract_features(soup)
                
                # Extract pricing
                scraped.pricing = self._extract_pricing(soup)
                
                # Extract testimonials
                scraped.testimonials = self._extract_testimonials(soup)
                
            elif markdown_content:
                # Fallback to markdown parsing if HTML not available
                scraped = self._parse_markdown(scraped, markdown_content)
            
            scraped.scrape_success = True
            
        except Exception as e:
            logger.error(f"Error extracting copy from {url}: {e}")
            scraped.scrape_success = False
            scraped.error_message = str(e)
        
        return scraped
    
    def _extract_ctas(self, soup: BeautifulSoup) -> List[str]:
        """Extract call-to-action buttons and links."""
        ctas = []
        
        # Find buttons
        for button in soup.find_all(['button', 'a'], class_=re.compile(r'(btn|button|cta)', re.I)):
            text = self._clean_text(button.get_text())
            if text and len(text) > 2 and len(text) < 50:
                ctas.append(text)
        
        # Find submit inputs
        for input_elem in soup.find_all('input', type='submit'):
            value = input_elem.get('value', '')
            if value:
                ctas.append(self._clean_text(value))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_ctas = []
        for cta in ctas:
            if cta.lower() not in seen:
                seen.add(cta.lower())
                unique_ctas.append(cta)
        
        return unique_ctas
    
    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract main body text from paragraphs."""
        paragraphs = []
        
        # Look for main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'(content|main)', re.I))
        
        if main_content:
            p_tags = main_content.find_all('p', limit=5)
        else:
            p_tags = soup.find_all('p', limit=5)
        
        for p in p_tags:
            text = self._clean_text(p.get_text())
            if text and len(text) > 20:  # Filter out short snippets
                paragraphs.append(text)
        
        # Join and limit to 1000 characters
        body_text = ' '.join(paragraphs)
        return body_text[:1000] if body_text else ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract feature lists from the page."""
        features = []
        
        # Look for feature sections
        feature_sections = soup.find_all(['ul', 'ol'], class_=re.compile(r'(feature|benefit|service)', re.I))
        
        if not feature_sections:
            # Look for any lists near headings containing keywords
            for heading in soup.find_all(['h2', 'h3'], string=re.compile(r'(feature|benefit|service|what we|why choose)', re.I)):
                next_sibling = heading.find_next_sibling()
                if next_sibling and next_sibling.name in ['ul', 'ol']:
                    feature_sections.append(next_sibling)
        
        for section in feature_sections[:2]:  # Limit to 2 sections
            for li in section.find_all('li', limit=10):
                text = self._clean_text(li.get_text())
                if text and len(text) > 5 and len(text) < 200:
                    features.append(text)
        
        return features[:20]  # Limit total features
    
    def _extract_pricing(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract pricing information."""
        pricing_patterns = [
            r'\$\d+(?:\.\d{2})?',  # $XX.XX
            r'\d+(?:\.\d{2})?\s*(?:USD|EUR|GBP)',  # XX.XX USD
            r'(?:starting at|from|only)\s*\$?\d+',  # starting at $XX
            r'\d+\s*(?:per|/)\s*(?:month|year|user)',  # XX per month
        ]
        
        # Look for pricing sections
        pricing_section = soup.find(class_=re.compile(r'(pric|cost|plan)', re.I))
        
        if pricing_section:
            text = pricing_section.get_text()
        else:
            # Search in full text
            text = soup.get_text()
        
        # Collect all price mentions
        price_mentions = []
        for pattern in pricing_patterns:
            matches = re.finditer(pattern, text, re.I)
            for match in matches:
                # Get some context around the price
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                price_context = self._clean_text(text[start:end])
                if price_context and price_context not in price_mentions:
                    price_mentions.append(price_context)
        
        # Return the most comprehensive pricing info
        if price_mentions:
            # Join unique price mentions
            return ' | '.join(price_mentions[:3])  # Limit to 3 price mentions
        
        return None
    
    def _extract_testimonials(self, soup: BeautifulSoup) -> List[str]:
        """Extract customer testimonials."""
        testimonials = []
        
        # Look for testimonial sections
        testimonial_sections = soup.find_all(class_=re.compile(r'(testimonial|review|quote)', re.I))
        
        for section in testimonial_sections[:5]:  # Limit to 5 testimonials
            # Look for quoted text
            blockquote = section.find('blockquote')
            if blockquote:
                text = self._clean_text(blockquote.get_text())
                if text and len(text) > 20:
                    testimonials.append(text[:500])  # Limit length
            else:
                # Look for any quoted-looking text
                text = self._clean_text(section.get_text())
                if text and (text.startswith('"') or text.startswith('"')):
                    testimonials.append(text[:500])
        
        return testimonials
    
    def _parse_markdown(self, scraped: ScrapedCopy, markdown: str) -> ScrapedCopy:
        """Parse markdown content as fallback."""
        lines = markdown.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract headline (# heading)
            if line.startswith('# ') and not scraped.headline:
                scraped.headline = line[2:].strip()
            
            # Extract subheadline (## heading)
            elif line.startswith('## ') and not scraped.subheadline:
                scraped.subheadline = line[3:].strip()
            
            # Look for links that might be CTAs
            elif '[' in line and '](' in line:
                match = re.search(r'\[([^\]]+)\]\([^\)]+\)', line)
                if match:
                    cta_text = match.group(1)
                    if len(cta_text) > 2 and len(cta_text) < 50:
                        if not scraped.cta:
                            scraped.cta = cta_text
                        else:
                            scraped.secondary_ctas.append(cta_text)
        
        # Extract body snippet from first few paragraphs
        paragraphs = [p for p in markdown.split('\n\n') if p and not p.startswith('#')]
        if paragraphs:
            scraped.body_snippet = ' '.join(paragraphs[:3])[:1000]
        
        return scraped
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def analyze_copy_trends(self, scraped_data: List[ScrapedCopy]) -> Dict[str, Any]:
        """
        Analyze trends across scraped landing pages.
        
        Args:
            scraped_data: List of ScrapedCopy objects
            
        Returns:
            Dictionary with trend analysis
        """
        analysis = {
            'total_pages': len(scraped_data),
            'successful_scrapes': sum(1 for s in scraped_data if s.scrape_success),
            'common_headline_words': [],
            'common_ctas': [],
            'common_features': [],
            'pricing_patterns': [],
            'average_word_counts': {},
            'cta_patterns': {},
            'keyword_frequency': []
        }
        
        # Collect all text elements
        all_headlines = []
        all_ctas = []
        all_features = []
        all_pricing = []
        word_counts = {'headline': [], 'body': [], 'cta': []}
        
        for scraped in scraped_data:
            if not scraped.scrape_success:
                continue
            
            # Collect headlines
            if scraped.headline:
                all_headlines.append(scraped.headline.lower())
                word_counts['headline'].append(len(scraped.headline.split()))
            
            # Collect CTAs
            if scraped.cta:
                all_ctas.append(scraped.cta)
                word_counts['cta'].append(len(scraped.cta.split()))
            
            all_ctas.extend(scraped.secondary_ctas)
            
            # Collect features
            all_features.extend(scraped.features)
            
            # Collect pricing
            if scraped.pricing:
                all_pricing.append(scraped.pricing)
            
            # Collect body word counts
            if scraped.body_snippet:
                word_counts['body'].append(len(scraped.body_snippet.split()))
        
        # Analyze headline words
        if all_headlines:
            headline_words = Counter()
            for headline in all_headlines:
                words = [w for w in headline.split() if len(w) > 3 and w.isalnum()]
                headline_words.update(words)
            
            analysis['common_headline_words'] = headline_words.most_common(15)
        
        # Analyze CTAs
        if all_ctas:
            cta_counter = Counter(all_ctas)
            analysis['common_ctas'] = cta_counter.most_common(10)
            
            # Analyze CTA patterns
            cta_starts = Counter()
            for cta in all_ctas:
                first_word = cta.split()[0].lower() if cta else ""
                if first_word:
                    cta_starts[first_word] += 1
            
            analysis['cta_patterns'] = {
                'common_starts': cta_starts.most_common(10),
                'average_length': sum(len(cta.split()) for cta in all_ctas) / len(all_ctas)
            }
        
        # Analyze features
        if all_features:
            feature_words = Counter()
            for feature in all_features:
                words = [w.lower() for w in feature.split() if len(w) > 4 and w.isalnum()]
                feature_words.update(words)
            
            analysis['common_features'] = feature_words.most_common(20)
        
        # Analyze pricing patterns
        if all_pricing:
            analysis['pricing_patterns'] = self._analyze_pricing_patterns(all_pricing)
        
        # Calculate average word counts
        for key, counts in word_counts.items():
            if counts:
                analysis['average_word_counts'][key] = sum(counts) / len(counts)
        
        # Extract keywords from all scraped content
        all_keywords = []
        for scraped in scraped_data:
            if scraped.scrape_success:
                all_keywords.extend(scraped.extract_keywords())
        
        if all_keywords:
            keyword_counter = Counter(all_keywords)
            analysis['keyword_frequency'] = keyword_counter.most_common(30)
        
        return analysis
    
    def _analyze_pricing_patterns(self, pricing_list: List[str]) -> Dict[str, Any]:
        """Analyze pricing patterns from extracted pricing text."""
        patterns = {
            'price_points': [],
            'pricing_models': Counter(),
            'currency': Counter()
        }
        
        for pricing_text in pricing_list:
            # Extract price points
            price_matches = re.findall(r'\$(\d+(?:\.\d{2})?)', pricing_text)
            for price in price_matches:
                try:
                    patterns['price_points'].append(float(price))
                except ValueError:
                    pass
            
            # Detect pricing models
            if re.search(r'per\s*(?:month|mo)', pricing_text, re.I):
                patterns['pricing_models']['monthly'] += 1
            if re.search(r'per\s*(?:year|yr|annual)', pricing_text, re.I):
                patterns['pricing_models']['yearly'] += 1
            if re.search(r'per\s*(?:user|seat)', pricing_text, re.I):
                patterns['pricing_models']['per_user'] += 1
            if re.search(r'one.?time|lifetime', pricing_text, re.I):
                patterns['pricing_models']['one_time'] += 1
            
            # Detect currency
            if '$' in pricing_text:
                patterns['currency']['USD'] += 1
            if '€' in pricing_text:
                patterns['currency']['EUR'] += 1
            if '£' in pricing_text:
                patterns['currency']['GBP'] += 1
        
        # Calculate price statistics
        if patterns['price_points']:
            patterns['price_stats'] = {
                'min': min(patterns['price_points']),
                'max': max(patterns['price_points']),
                'average': sum(patterns['price_points']) / len(patterns['price_points'])
            }
        
        patterns['pricing_models'] = dict(patterns['pricing_models'].most_common())
        patterns['currency'] = dict(patterns['currency'].most_common())
        
        return patterns
    
    def generate_copy_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate actionable insights from copy analysis.
        
        Args:
            analysis: Output from analyze_copy_trends
            
        Returns:
            List of insights/recommendations
        """
        insights = []
        
        # Headline insights
        if analysis['common_headline_words']:
            top_words = [word for word, _ in analysis['common_headline_words'][:5]]
            insights.append(f"Top headline keywords: {', '.join(top_words)}")
            insights.append("Consider incorporating these terms in your headlines for better resonance")
        
        # CTA insights
        if analysis['common_ctas']:
            top_ctas = [cta for cta, _ in analysis['common_ctas'][:3]]
            insights.append(f"Most common CTAs: {', '.join(top_ctas)}")
            
            if 'cta_patterns' in analysis:
                avg_length = analysis['cta_patterns'].get('average_length', 0)
                insights.append(f"Average CTA length: {avg_length:.1f} words")
        
        # Pricing insights
        if 'pricing_patterns' in analysis:
            pricing = analysis['pricing_patterns']
            if 'price_stats' in pricing:
                stats = pricing['price_stats']
                insights.append(f"Price range: ${stats['min']:.2f} - ${stats['max']:.2f} (avg: ${stats['average']:.2f})")
            
            if pricing.get('pricing_models'):
                top_model = max(pricing['pricing_models'], key=pricing['pricing_models'].get)
                insights.append(f"Most common pricing model: {top_model}")
        
        # Word count insights
        if analysis.get('average_word_counts'):
            counts = analysis['average_word_counts']
            if 'headline' in counts:
                insights.append(f"Average headline length: {counts['headline']:.1f} words")
            if 'body' in counts:
                insights.append(f"Average body text length: {counts['body']:.1f} words")
        
        # Feature insights
        if analysis['common_features']:
            top_features = [word for word, _ in analysis['common_features'][:5]]
            insights.append(f"Common feature keywords: {', '.join(top_features)}")
        
        # Success rate
        if analysis['total_pages'] > 0:
            success_rate = (analysis['successful_scrapes'] / analysis['total_pages']) * 100
            insights.append(f"Scraping success rate: {success_rate:.1f}%")
        
        return insights