"""
Sitemap Crawler Module
Handles sitemap discovery and URL extraction with async support
Supports both fast mode (requests) and browser mode (Playwright in subprocess)
"""
import asyncio
import requests
import subprocess
import sys
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import re
import logging
from common.config import (
    SITEMAP_PATTERNS, POST_URL_PATTERNS, EXCLUDE_URL_PATTERNS,
    DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)

logger = logging.getLogger(__name__)

# Path to standalone Playwright fetcher
PLAYWRIGHT_FETCHER = Path(__file__).parent / "playwright_fetcher.py"
PLAYWRIGHT_AVAILABLE = PLAYWRIGHT_FETCHER.exists()




class SitemapCrawler:
    """Crawls and extracts URLs from sitemaps"""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES, use_browser: bool = False):
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_browser = use_browser and PLAYWRIGHT_AVAILABLE
        self.session = None
        
        if use_browser and not PLAYWRIGHT_AVAILABLE:
            logger.warning("Browser mode requested but playwright_fetcher.py not found - falling back to fast mode")
            self.use_browser = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_browser:
            logger.info("Starting browser mode (Playwright subprocess)")
        else:
            logger.info("Starting fast mode (requests)")
            
        self.session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            self.session.close()
    
    async def fetch_url(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch URL content with retry logic"""
        if self.use_browser:
            return await self._fetch_url_browser(url, retry_count)
        else:
            return await self._fetch_url_requests(url, retry_count)
    
    async def _fetch_url_browser(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch URL using Playwright in subprocess (visual or headless)"""
        try:
            # Run Playwright fetcher in subprocess
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_playwright_subprocess,
                url
            )
            
            if result:
                logger.info(f"Successfully fetched {url} via browser ({len(result)} bytes)")
                return result
            else:
                logger.warning(f"Failed to fetch {url} via browser")
                if retry_count < self.max_retries:
                    await asyncio.sleep(RETRY_DELAY)
                    return await self._fetch_url_browser(url, retry_count + 1)
                return None
                
        except Exception as e:
            logger.error(f"Browser error fetching {url}: {str(e)}")
            if retry_count < self.max_retries:
                await asyncio.sleep(RETRY_DELAY)
                return await self._fetch_url_browser(url, retry_count + 1)
            return None
    
    def _run_playwright_subprocess(self, url: str) -> Optional[str]:
        """Run Playwright fetcher as subprocess"""
        try:
            # Use headless mode by default (add --headless flag)
            # Remove --headless to see the browser window
            cmd = [sys.executable, str(PLAYWRIGHT_FETCHER), url, "--headless"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 10
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                logger.error(f"Playwright subprocess failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Playwright subprocess timed out for {url}")
            return None
        except Exception as e:
            logger.error(f"Subprocess error: {str(e)}")
            return None
    
    async def _fetch_url_requests(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch URL using requests library (async wrapper)"""
        try:
            # Run requests.get in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(url, timeout=self.timeout, allow_redirects=True, verify=False)
            )
            
            if response.status_code == 200:
                content = response.text
                logger.info(f"Successfully fetched {url} ({len(content)} bytes)")
                return content
            elif response.status_code in [429, 503] and retry_count < self.max_retries:
                # Rate limited, wait and retry
                await asyncio.sleep(RETRY_DELAY * (retry_count + 1))
                return await self._fetch_url_requests(url, retry_count + 1)
            else:
                logger.warning(f"Failed to fetch {url}: Status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                logger.warning(f"Timeout for {url}, retrying... ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(RETRY_DELAY)
                return await self._fetch_url_requests(url, retry_count + 1)
            else:
                logger.error(f"Max retries exceeded for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            if retry_count < self.max_retries:
                await asyncio.sleep(RETRY_DELAY)
                return await self._fetch_url_requests(url, retry_count + 1)
            return None
    
    async def check_robots_txt(self, base_url: str) -> List[str]:
        """Check robots.txt for sitemap URLs"""
        robots_url = urljoin(base_url, '/robots.txt')
        content = await self.fetch_url(robots_url)
        
        if not content:
            return []
        
        sitemap_urls = []
        for line in content.split('\n'):
            if line.strip().lower().startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                sitemap_urls.append(sitemap_url)
        
        logger.info(f"Found {len(sitemap_urls)} sitemaps in robots.txt for {base_url}")
        return sitemap_urls
    
    async def discover_sitemap(self, base_url: str, 
                              custom_patterns: List[str] = None) -> Optional[str]:
        """
        Discover sitemap URL for a website
        Tries common patterns first, then checks robots.txt
        """
        # Normalize base URL
        if not base_url.startswith('http'):
            base_url = 'https://' + base_url
        
        parsed = urlparse(base_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Combine default and custom patterns
        patterns = SITEMAP_PATTERNS.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)
        
        # Try common sitemap patterns
        logger.info(f"Discovering sitemap for {base_url}")
        for pattern in patterns:
            sitemap_url = base_url + pattern
            content = await self.fetch_url(sitemap_url)
            
            if content and self._is_valid_sitemap(content):
                logger.info(f"Found sitemap: {sitemap_url}")
                return sitemap_url
        
        # Check robots.txt
        robots_sitemaps = await self.check_robots_txt(base_url)
        for sitemap_url in robots_sitemaps:
            content = await self.fetch_url(sitemap_url)
            if content and self._is_valid_sitemap(content):
                logger.info(f"Found sitemap from robots.txt: {sitemap_url}")
                return sitemap_url
        
        logger.warning(f"No sitemap found for {base_url}")
        return None
    
    def _is_valid_sitemap(self, content: str) -> bool:
        """Check if content is a valid sitemap"""
        return '<urlset' in content or '<sitemapindex' in content
    
    async def parse_sitemap(self, sitemap_url: str) -> Dict[str, any]:
        """
        Parse a sitemap and extract all URLs
        Handles both regular sitemaps and sitemap indexes
        """
        content = await self.fetch_url(sitemap_url)
        if not content:
            return {'urls': [], 'nested_sitemaps': [], 'error': 'Failed to fetch sitemap'}
        
        soup = BeautifulSoup(content, 'xml')
        
        result = {
            'urls': [],
            'nested_sitemaps': [],
            'is_index': False
        }
        
        # Check if it's a sitemap index
        if soup.find('sitemapindex'):
            result['is_index'] = True
            sitemap_tags = soup.find_all('sitemap')
            for sitemap in sitemap_tags:
                loc = sitemap.find('loc')
                if loc:
                    nested_url = loc.text.strip()
                    # Convert http:// to https:// for consistency
                    if nested_url.startswith('http://'):
                        nested_url = nested_url.replace('http://', 'https://', 1)
                    result['nested_sitemaps'].append(nested_url)
            logger.info(f"Found sitemap index with {len(result['nested_sitemaps'])} nested sitemaps")
        else:
            # Regular sitemap with URLs
            url_tags = soup.find_all('url')
            for url_tag in url_tags:
                loc = url_tag.find('loc')
                if loc:
                    url = loc.text.strip()
                    # Convert http:// to https:// for consistency
                    if url.startswith('http://'):
                        url = url.replace('http://', 'https://', 1)
                    result['urls'].append(url)
            logger.info(f"Found {len(result['urls'])} URLs in sitemap")
        
        return result
    
    async def get_all_sitemap_urls(self, sitemap_url: str, 
                                   post_patterns: List[str] = None,
                                   exclude_patterns: List[str] = None) -> List[str]:
        """
        Recursively get all URLs from sitemap, including nested sitemaps
        Filters URLs based on post patterns and exclusion rules
        """
        all_urls = []
        visited_sitemaps = set()
        
        async def process_sitemap(url: str):
            if url in visited_sitemaps:
                logger.debug(f"Already visited sitemap: {url}")
                return
            
            logger.info(f"Processing sitemap: {url}")
            visited_sitemaps.add(url)
            
            # Add small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
            
            result = await self.parse_sitemap(url)
            
            if 'error' in result:
                logger.error(f"Error parsing {url}: {result['error']}")
                return
            
            # Process nested sitemaps recursively (with concurrency limit)
            if result['nested_sitemaps']:
                logger.info(f"Found {len(result['nested_sitemaps'])} nested sitemaps in {url}")
                for nested_url in result['nested_sitemaps']:
                    logger.info(f"  - Nested sitemap: {nested_url}")
                
                # Process nested sitemaps sequentially to avoid rate limiting
                for nested_url in result['nested_sitemaps']:
                    await process_sitemap(nested_url)
            
            # Add URLs from this sitemap (without filtering yet - collect all first)
            if result['urls']:
                logger.info(f"Found {len(result['urls'])} URLs in {url}")
                all_urls.extend(result['urls'])
            else:
                logger.info(f"No URLs found in {url} (might be an index)")
        
        await process_sitemap(sitemap_url)
        
        # Now filter all collected URLs
        if all_urls:
            filtered_urls = self._filter_post_urls(
                all_urls, 
                post_patterns or POST_URL_PATTERNS,
                exclude_patterns or EXCLUDE_URL_PATTERNS
            )
            unique_urls = list(set(filtered_urls))  # Remove duplicates
            logger.info(f"Total URLs extracted: {len(unique_urls)} (from {len(all_urls)} before filtering/deduplication)")
            return unique_urls
        else:
            logger.warning("No URLs found in any sitemap")
            return []
    
    def _filter_post_urls(self, urls: List[str], 
                         post_patterns: List[str],
                         exclude_patterns: List[str]) -> List[str]:
        """Filter URLs to include only posts and exclude unwanted pages"""
        filtered_urls = []
        
        logger.info(f"Filtering {len(urls)} URLs with {len(post_patterns)} post patterns and {len(exclude_patterns)} exclude patterns")
        
        # First pass: check if ANY URL matches the post patterns
        pattern_matched_count = 0
        for url in urls:
            for pattern in post_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    pattern_matched_count += 1
                    break
        
        # If no URLs match the post patterns, fall back to permissive mode
        # (include all URLs that aren't explicitly excluded)
        use_permissive_mode = (pattern_matched_count == 0 and post_patterns)
        if use_permissive_mode:
            logger.warning(f"No URLs matched post patterns - using permissive mode (include all non-excluded URLs)")
        
        for url in urls:
            # Check if URL should be excluded
            should_exclude = False
            for pattern in exclude_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    logger.debug(f"Excluding URL {url} (matched exclude pattern: {pattern})")
                    should_exclude = True
                    break
            
            if should_exclude:
                continue
            
            # Check if URL matches post patterns
            if not post_patterns or use_permissive_mode:
                # No patterns or permissive mode - include all non-excluded URLs
                logger.debug(f"Including URL: {url}")
                filtered_urls.append(url)
            else:
                # Try to match any post pattern
                matched = False
                for pattern in post_patterns:
                    if re.search(pattern, url, re.IGNORECASE):
                        matched = True
                        logger.debug(f"URL {url} matched post pattern: {pattern}")
                        break
                
                # Only include if it matched a post pattern
                if matched:
                    filtered_urls.append(url)
                else:
                    logger.debug(f"URL {url} didn't match any post pattern - excluding")
        
        logger.info(f"Filtered to {len(filtered_urls)} URLs (permissive_mode={use_permissive_mode})")
        return filtered_urls
        
        logger.info(f"Filtered {len(urls)} URLs down to {len(filtered_urls)} URLs")
        return filtered_urls
    
    async def crawl_site_sitemap(self, site_url: str, 
                                 custom_sitemap: str = None,
                                 manual_xml: str = None,
                                 custom_patterns: List[str] = None,
                                 post_patterns: List[str] = None,
                                 exclude_patterns: List[str] = None) -> Dict:
        """
        Main method to crawl a site's sitemap and extract all post URLs
        
        Args:
            manual_xml: If provided, parse this XML content directly instead of fetching
        
        Returns:
            Dict with sitemap_url, total_urls, urls, and status
        """
        try:
            # Use manual XML if provided (bypass connection issues)
            if manual_xml:
                logger.info("Using manually pasted XML content")
                sitemap_url = custom_sitemap or site_url + "/sitemap.xml"
                urls = await self._parse_manual_xml(
                    manual_xml,
                    sitemap_url,
                    post_patterns,
                    exclude_patterns
                )
                
                return {
                    'status': 'success',
                    'sitemap_url': sitemap_url,
                    'total_urls': len(urls),
                    'urls': urls,
                    'message': f'Successfully extracted {len(urls)} post URLs from manual XML'
                }
            
            # Discover sitemap
            if custom_sitemap:
                sitemap_url = custom_sitemap
            else:
                sitemap_url = await self.discover_sitemap(site_url, custom_patterns)
            
            if not sitemap_url:
                return {
                    'status': 'no_sitemap',
                    'sitemap_url': None,
                    'total_urls': 0,
                    'urls': [],
                    'message': 'No sitemap found. Please provide manual sitemap URL.'
                }
            
            # Extract all URLs
            urls = await self.get_all_sitemap_urls(
                sitemap_url,
                post_patterns,
                exclude_patterns
            )
            
            return {
                'status': 'success',
                'sitemap_url': sitemap_url,
                'total_urls': len(urls),
                'urls': urls,
                'message': f'Successfully extracted {len(urls)} post URLs'
            }
            
        except Exception as e:
            logger.error(f"Error crawling sitemap for {site_url}: {str(e)}")
            return {
                'status': 'error',
                'sitemap_url': None,
                'total_urls': 0,
                'urls': [],
                'message': f'Error: {str(e)}'
            }
    
    async def _parse_manual_xml(self, xml_content: str, sitemap_url: str,
                               post_patterns: List[str] = None,
                               exclude_patterns: List[str] = None) -> List[str]:
        """Parse manually pasted XML content"""
        all_urls = []
        
        soup = BeautifulSoup(xml_content, 'xml')
        
        # Check if it's a sitemap index
        if soup.find('sitemapindex'):
            # Extract nested sitemap URLs
            sitemap_tags = soup.find_all('sitemap')
            nested_sitemaps = []
            for sitemap in sitemap_tags:
                loc = sitemap.find('loc')
                if loc:
                    nested_url = loc.text.strip()
                    nested_sitemaps.append(nested_url)
            
            logger.warning(f"Manual XML is a sitemap index with {len(nested_sitemaps)} nested sitemaps. You'll need to paste each one separately:")
            for url in nested_sitemaps:
                logger.info(f"  - {url}")
            
            return []  # Can't auto-fetch nested sitemaps in manual mode
        else:
            # Regular sitemap with URLs
            url_tags = soup.find_all('url')
            for url_tag in url_tags:
                loc = url_tag.find('loc')
                if loc:
                    url = loc.text.strip()
                    all_urls.append(url)
            
            logger.info(f"Extracted {len(all_urls)} URLs from manual XML")
            
            # Filter URLs
            filtered_urls = self._filter_post_urls(
                all_urls,
                post_patterns or POST_URL_PATTERNS,
                exclude_patterns or EXCLUDE_URL_PATTERNS
            )
            
            return list(set(filtered_urls))


async def discover_multiple_sites(sites: List[str], 
                                  concurrent: int = 10) -> Dict[str, Dict]:
    """
    Discover sitemaps for multiple sites concurrently
    
    Args:
        sites: List of site URLs
        concurrent: Number of concurrent requests
        
    Returns:
        Dict mapping site URL to discovery result
    """
    results = {}
    
    async with SitemapCrawler() as crawler:
        semaphore = asyncio.Semaphore(concurrent)
        
        async def discover_with_limit(site_url: str):
            async with semaphore:
                result = await crawler.crawl_site_sitemap(site_url)
                results[site_url] = result
        
        tasks = [discover_with_limit(site) for site in sites]
        await asyncio.gather(*tasks)
    
    return results
