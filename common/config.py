"""
Configuration settings for the Web Crawler Application
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Database configuration
DB_PATH = BASE_DIR / "crawler_data.db"

# Crawler settings
DEFAULT_THREADS = 20
MAX_THREADS = 100
MIN_THREADS = 1
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Rate limiting
DEFAULT_DELAY = 0.1  # seconds between requests
MAX_DELAY = 5.0
RATE_LIMIT_ERRORS = ['429', '503', 'too many requests']

# Sitemap patterns to check
SITEMAP_PATTERNS = [
    '/sitemap.xml',
    '/sitemap_index.xml',
    '/wp-sitemap.xml',
    '/sitemap-index.xml',
    '/post-sitemap.xml',
    '/news-sitemap.xml',
    '/sitemap-news.xml',
    '/page-sitemap.xml',
    '/article-sitemap.xml',
    '/sitemap1.xml',
    '/sitemap_posts.xml',
    '/blog-sitemap.xml',
    '/main-sitemap.xml',
    '/index-sitemap.xml',
    # Yoast SEO patterns
    '/sitemap_index.xml',
    '/post-sitemap.xml',
    '/page-sitemap.xml',
    '/category-sitemap.xml',
    # RankMath patterns
    '/sitemap.xml',
    '/sitemap_index.xml',
]

# Post URL patterns (to identify posts vs pages/categories)
POST_URL_PATTERNS = [
    '/blog/',
    '/article/',
    '/news/',
    '/post/',
    '/story/',
    r'/\d{4}/\d{2}/',  # Date-based URLs like /2024/01/
]

# URL patterns to exclude (categories, pages, etc.)
EXCLUDE_URL_PATTERNS = [
    '/category/',
    '/tag/',
    '/author/',
    '/page/',
    r'/about/?$',
    r'/contact/?$',
    r'/privacy/?$',
    r'/terms/?$',
]

# Domains to exclude from outgoing links (social media, trackers)
DEFAULT_EXCLUDED_DOMAINS = [
    'facebook.com',
    'twitter.com',
    'x.com',
    'instagram.com',
    'linkedin.com',
    'pinterest.com',
    'youtube.com',
    'tiktok.com',
    'reddit.com',
    'google.com',
    'google-analytics.com',
    'googletagmanager.com',
    'doubleclick.net',
    'facebook.net',
    'fbcdn.net',
    'google.com',
    'gstatic.com',
    't.co',
    'bit.ly',
    'ow.ly',
    'tinyurl.com',
]

# Link attributes to filter
FILTER_LINK_ATTRIBUTES = ['nofollow', 'sponsored', 'ugc']

# Content selectors (priority order)
CONTENT_SELECTORS = [
    'article',
    '[role="main"]',
    'main',
    '.post-content',
    '.entry-content',
    '.article-content',
    '#content',
    '.content',
]

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "crawler.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# UI Configuration
PAGE_TITLE = "Advanced Web Crawler & Backlink Analyzer"
PAGE_ICON = "🔍"
LAYOUT = "wide"

# Colors (Light theme)
COLORS = {
    'primary': '#4A90E2',
    'success': '#7ED321',
    'warning': '#F5A623',
    'error': '#D0021B',
    'info': '#50E3C2',
    'background': '#F8F9FA',
    'text': '#333333',
}

# Export settings
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
