"""
Link Extractor Module
Extracts outgoing links from web pages with async support
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import re
import logging
from playwright.async_api import async_playwright
from common.config import (
    DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_DELAY, CONTENT_SELECTORS,
    FILTER_LINK_ATTRIBUTES, DEFAULT_EXCLUDED_DOMAINS
)

logger = logging.getLogger(__name__)


class LinkExtractor:
    """Extracts outgoing links from web pages"""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, 
                 max_retries: int = MAX_RETRIES,
                 use_playwright: bool = False):
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_playwright = use_playwright
        self.session = None
        self.playwright = None
        self.browser = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
        else:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.session:
            await self.session.close()
    
    async def fetch_with_requests(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch URL using aiohttp"""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status in [429, 503] and retry_count < self.max_retries:
                    await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                    return await self.fetch_with_requests(url, retry_count + 1)
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
        except asyncio.TimeoutError:
            if retry_count < self.max_retries:
                logger.warning(f"Timeout for {url}, retrying... ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(RETRY_DELAY)
                return await self.fetch_with_requests(url, retry_count + 1)
            else:
                logger.error(f"Max retries exceeded for {url}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    async def fetch_with_playwright(self, url: str, retry_count: int = 0, screenshot_path: str = None) -> Optional[str]:
        """Fetch URL using Playwright (for JavaScript-heavy sites)"""
        try:
            page = await self.browser.new_page()
            # Set viewport for consistent screenshots
            await page.set_viewport_size({"width": 1280, "height": 800})
            
            await page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            if screenshot_path:
                try:
                    await page.screenshot(path=screenshot_path)
                except Exception as e:
                    logger.warning(f"Failed to take screenshot for {url}: {e}")
            
            content = await page.content()
            await page.close()
            return content
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Playwright error for {url}, retrying... ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(RETRY_DELAY)
                return await self.fetch_with_playwright(url, retry_count + 1, screenshot_path)
            else:
                logger.error(f"Playwright failed for {url}: {str(e)}")
                return None
    
    async def fetch_page(self, url: str, screenshot_path: str = None) -> Optional[str]:
        """Fetch page content (uses appropriate method)"""
        if self.use_playwright:
            return await self.fetch_with_playwright(url, screenshot_path=screenshot_path)
        else:
            return await self.fetch_with_requests(url)
    
    def _get_article_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract article content from page using content selectors"""
        for selector in CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                logger.debug(f"Found content using selector: {selector}")
                return content
        
        # If no specific content area found, use body
        logger.debug("No specific content area found, using body")
        return soup.find('body')
    
    def _calculate_link_position(self, link_element, article_content) -> Dict[str, int]:
        """Calculate link position in terms of paragraph and word count"""
        position = {
            'paragraph': 0,
            'word': 0
        }
        
        try:
            # Find all paragraphs before this link
            all_paragraphs = article_content.find_all(['p', 'div', 'section'])
            link_paragraph = link_element.find_parent(['p', 'div', 'section'])
            
            if link_paragraph:
                # Count paragraphs before this one
                for idx, p in enumerate(all_paragraphs, 1):
                    if p == link_paragraph:
                        position['paragraph'] = idx
                        break
            
            # Calculate word position
            text_before = ''
            for elem in article_content.find_all(text=True):
                parent = elem.parent
                if parent and parent == link_element:
                    break
                text_before += elem
            
            position['word'] = len(text_before.split())
            
        except Exception as e:
            logger.debug(f"Error calculating position: {str(e)}")
        
        return position
    
    def _is_external_link(self, link_url: str, base_domain: str) -> bool:
        """Check if link is external (not same domain)"""
        try:
            link_domain = urlparse(link_url).netloc
            return link_domain != base_domain and link_domain != ''
        except:
            return False
    
    def _should_exclude_link(self, link_url: str, excluded_domains: List[str]) -> bool:
        """Check if link should be excluded based on domain"""
        try:
            link_domain = urlparse(link_url).netloc.lower()
            # Remove www. for comparison
            link_domain = link_domain.replace('www.', '')
            
            for excluded in excluded_domains:
                excluded = excluded.lower().replace('www.', '')
                if excluded in link_domain or link_domain in excluded:
                    return True
            return False
        except:
            return True  # Exclude if we can't parse
    
    def _should_filter_by_attributes(self, link_element) -> bool:
        """Check if link should be filtered based on rel attributes"""
        rel_attr = link_element.get('rel', [])
        if isinstance(rel_attr, str):
            rel_attr = [rel_attr]
        
        # Check if any filter attribute is present
        for attr in FILTER_LINK_ATTRIBUTES:
            if attr in rel_attr:
                return True
        return False
    
    def _extract_links_from_element(self, element, base_url: str, 
                                   base_domain: str, excluded_domains: List[str],
                                   is_article: bool = True) -> List[Dict]:
        """Extract links from a specific element"""
        links = []
        
        for link in element.find_all('a', href=True):
            href = link.get('href', '').strip()
            
            # Skip empty links, anchors, javascript, mailto, tel
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Check if external link
            if not self._is_external_link(absolute_url, base_domain):
                continue
            
            # Check if should be excluded
            if self._should_exclude_link(absolute_url, excluded_domains):
                continue
            
            # Check rel attributes (optionally filter)
            # filter_by_rel = self._should_filter_by_attributes(link)
            
            # Extract link data
            link_data = {
                'url': absolute_url,
                'anchor_text': link.get_text(strip=True)[:500],  # Limit anchor text length
                'rel_attributes': ','.join(link.get('rel', [])) if link.get('rel') else None,
                'target': link.get('target'),
                'is_article_link': is_article
            }
            
            # Calculate position if it's an article link
            if is_article:
                position = self._calculate_link_position(link, element)
                link_data['position_paragraph'] = position['paragraph']
                link_data['position_word'] = position['word']
            
            links.append(link_data)
        
        return links
    
    def _extract_links_from_headings(self, soup: BeautifulSoup, base_url: str,
                                    base_domain: str, excluded_domains: List[str]) -> List[Dict]:
        """Extract links from H2 headings"""
        links = []
        
        for h2 in soup.find_all('h2'):
            h2_links = self._extract_links_from_element(
                h2, base_url, base_domain, excluded_domains, is_article=False
            )
            for link in h2_links:
                link['link_location'] = 'h2_heading'
            links.extend(h2_links)
        
        return links
    
    def _extract_sidebar_links(self, soup: BeautifulSoup, article_element,
                               base_url: str, base_domain: str, 
                               excluded_domains: List[str]) -> List[Dict]:
        """Extract links from sidebar, blogroll, etc."""
        links = []
        
        # Common sidebar selectors
        sidebar_selectors = [
            'aside', '.sidebar', '#sidebar', '.widget', 
            '.blogroll', '.related-posts', '.sticky'
        ]
        
        for selector in sidebar_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Skip if this element is inside the article
                if article_element and element in article_element.descendants:
                    continue
                
                elem_links = self._extract_links_from_element(
                    element, base_url, base_domain, excluded_domains, is_article=False
                )
                
                for link in elem_links:
                    link['link_location'] = selector
                
                links.extend(elem_links)
        
        return links
    
    async def extract_outgoing_links(self, url: str, 
                                    excluded_domains: List[str] = None,
                                    screenshot_path: str = None) -> Dict:
        """
        Extract all outgoing links from a page
        
        Returns:
            Dict with status, total_links, links (list), and metadata
        """
        try:
            # Fetch page content
            content = await self.fetch_page(url, screenshot_path=screenshot_path)
            
            if not content:
                return {
                    'status': 'error',
                    'total_links': 0,
                    'links': [],
                    'message': 'Failed to fetch page'
                }
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get base domain
            parsed_url = urlparse(url)
            base_domain = parsed_url.netloc
            
            # Use default excluded domains if none provided
            if excluded_domains is None:
                excluded_domains = DEFAULT_EXCLUDED_DOMAINS
            
            all_links = []
            
            # Extract links from article content
            article_content = self._get_article_content(soup)
            if article_content:
                article_links = self._extract_links_from_element(
                    article_content, url, base_domain, excluded_domains, is_article=True
                )
                for link in article_links:
                    link['link_location'] = 'article'
                all_links.extend(article_links)
            
            # Extract links from H2 headings
            h2_links = self._extract_links_from_headings(
                soup, url, base_domain, excluded_domains
            )
            all_links.extend(h2_links)
            
            # Extract sidebar/blogroll links
            sidebar_links = self._extract_sidebar_links(
                soup, article_content, url, base_domain, excluded_domains
            )
            all_links.extend(sidebar_links)
            
            # Remove duplicates while preserving first occurrence
            seen_urls = set()
            unique_links = []
            for link in all_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            logger.info(f"Extracted {len(unique_links)} unique outgoing links from {url}")
            
            return {
                'status': 'success',
                'total_links': len(unique_links),
                'links': unique_links,
                'message': f'Successfully extracted {len(unique_links)} outgoing links'
            }
            
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {str(e)}")
            return {
                'status': 'error',
                'total_links': 0,
                'links': [],
                'message': f'Error: {str(e)}'
            }


async def extract_from_multiple_pages(post_urls: List[str],
                                      excluded_domains: List[str] = None,
                                      concurrent: int = 20,
                                      use_playwright: bool = False,
                                      progress_callback = None) -> Dict[str, Dict]:
    """
    Extract outgoing links from multiple pages concurrently
    
    Args:
        post_urls: List of post URLs to crawl
        excluded_domains: List of domains to exclude
        concurrent: Number of concurrent requests
        use_playwright: Whether to use Playwright for JavaScript sites
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Dict mapping post URL to extraction result
    """
    results = {}
    completed = 0
    total = len(post_urls)
    
    async with LinkExtractor(use_playwright=use_playwright) as extractor:
        semaphore = asyncio.Semaphore(concurrent)
        
        async def extract_with_limit(post_url: str):
            nonlocal completed
            async with semaphore:
                result = await extractor.extract_outgoing_links(post_url, excluded_domains)
                results[post_url] = result
                completed += 1
                
                if progress_callback:
                    await progress_callback(completed, total, post_url)
                
                return result
        
        tasks = [extract_with_limit(url) for url in post_urls]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    return results


async def batch_extract_with_fallback(post_urls: List[str],
                                      excluded_domains: List[str] = None,
                                      concurrent: int = 20,
                                      progress_callback = None) -> Dict[str, Dict]:
    """
    Extract links using requests first, fallback to Playwright for failures
    
    This is the recommended method for maximum efficiency
    """
    # First pass: Use fast requests-based extraction
    logger.info(f"Starting extraction for {len(post_urls)} posts with requests...")
    results = await extract_from_multiple_pages(
        post_urls, excluded_domains, concurrent, False, progress_callback
    )
    
    # Find failed extractions
    failed_urls = [url for url, result in results.items() 
                   if result['status'] == 'error' or result['total_links'] == 0]
    
    if failed_urls:
        logger.info(f"Retrying {len(failed_urls)} failed URLs with Playwright...")
        # Second pass: Retry failed URLs with Playwright
        playwright_results = await extract_from_multiple_pages(
            failed_urls, excluded_domains, min(concurrent // 2, 10), True, progress_callback
        )
        
        # Update results with Playwright extractions
        results.update(playwright_results)
    
    return results
