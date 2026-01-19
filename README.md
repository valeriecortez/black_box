# Advanced Web Crawler & Backlink Analyzer

A professional web application for crawling websites, extracting sitemaps, and analyzing outgoing backlinks.

## 🌟 Features

### Core Functionality
- **Sitemap Discovery**: Automatically detects sitemaps using common patterns and robots.txt
- **Smart Crawling**: Differentiates between posts, pages, and categories
- **Link Extraction**: Extracts outgoing links with detailed metadata
- **Concurrent Processing**: High-speed async crawling with adjustable threads (1-100)
- **Fallback Support**: Automatic fallback to Playwright for JavaScript-heavy sites

### Data Management
- **SQLite Database**: Professional data storage with proper indexing
- **Crawl History**: Tracks all crawl operations with timestamps
- **Error Logging**: Comprehensive error tracking with retry support
- **Incremental Updates**: Re-crawls only new/updated content

### Link Analysis
- **Position Tracking**: Records paragraph and word position of each link
- **Link Classification**: Identifies article links vs sidebar/blogroll links
- **Attribute Filtering**: Tracks rel attributes (nofollow, sponsored, ugc)
- **Domain Exclusion**: Filter out social media and tracking domains

### Export & Reporting
- **Multiple Formats**: Export to CSV, Excel, or JSON
- **Flexible Selection**: Export individual sites or complete datasets
- **Unique Links Option**: Export deduplicated links when needed
- **Multi-sheet Reports**: Comprehensive Excel reports with multiple sheets

### User Interface
- **Clean Dashboard**: Real-time statistics and progress tracking
- **Professional Design**: Light-themed, responsive interface
- **Progress Monitoring**: Live progress bars and status updates
- **Batch Operations**: Process multiple sites simultaneously

## 📋 Requirements

- Python 3.8+
- Windows/Linux/Mac OS
- Minimum 4GB RAM (8GB+ recommended for large crawls)

## 🚀 Installation

### 1. Clone or Download
```bash
cd "j:\new testing scripts"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers (if using JavaScript crawling)
```bash
playwright install chromium
```

## 🎯 Usage

### Starting the Application

#### Local Machine
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

#### Remote Server
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Quick Start Guide

1. **Add Sites**
   - Go to "🌐 Manage Sites"
   - Enter website URL(s)
   - Optionally add custom sitemap URL

2. **Crawl Sitemap**
   - Go to "🗺️ Sitemap Crawler"
   - Select site(s) to crawl
   - Click "Start Crawl"
   - System will discover and parse sitemaps

3. **Extract Links**
   - Go to "🔗 Link Extractor"
   - Select site
   - Adjust thread count (default: 20)
   - Click "Start Link Extraction"

4. **Export Data**
   - Go to "📥 Export Data"
   - Choose export type
   - Select format (CSV/Excel/JSON)
   - Download results

## ⚙️ Configuration

### Crawler Settings

Edit `config.py` to customize:

- **DEFAULT_THREADS**: Default concurrent threads (default: 20)
- **MAX_THREADS**: Maximum allowed threads (default: 100)
- **DEFAULT_TIMEOUT**: Request timeout in seconds (default: 30)
- **MAX_RETRIES**: Number of retry attempts (default: 3)

### Sitemap Patterns

Add custom sitemap patterns in `config.py`:
```python
SITEMAP_PATTERNS = [
    '/sitemap.xml',
    '/your-custom-pattern.xml',
    # Add more patterns
]
```

### Post URL Patterns

Define patterns to identify post URLs:
```python
POST_URL_PATTERNS = [
    '/blog/',
    '/article/',
    '/news/',
    # Add more patterns
]
```

### Excluded Domains

Add domains to exclude in Settings page or in `config.py`:
```python
DEFAULT_EXCLUDED_DOMAINS = [
    'facebook.com',
    'twitter.com',
    # Add more domains
]
```

## 📊 Database Structure

The application uses SQLite with the following main tables:

- **sites**: Website information and statistics
- **sitemap_urls**: Discovered sitemap URLs
- **posts**: Individual post/article URLs
- **outgoing_links**: Extracted outgoing links with metadata
- **crawl_history**: Crawl operation logs
- **error_logs**: Error tracking and retry information

## 🔧 Advanced Features

### Concurrent Crawling

**Single Site with Multiple Threads**
- Crawls one site at a time using multiple threads for posts
- Best for detailed analysis of individual sites
- Recommended: 20-50 threads

**Multiple Sites Simultaneously**
- Crawls different sites concurrently
- Best for bulk sitemap discovery
- Recommended: 5-10 concurrent sites

### Visual vs Silent Mode

**Silent Mode** (Default)
- No browser windows
- Fast async HTTP requests
- Best for most sites

**Visual Mode** (Playwright)
- Headless browser rendering
- Handles JavaScript-heavy sites
- Automatically used as fallback

### Link Position Tracking

Each extracted link includes:
- **Paragraph Number**: Which paragraph contains the link
- **Word Count**: Position in words from article start
- **Link Location**: Where the link appears (article, sidebar, h2, etc.)

## 📁 File Structure

```
new testing scripts/
├── app.py                  # Main Streamlit application
├── config.py               # Configuration settings
├── database.py             # Database operations
├── sitemap_crawler.py      # Sitemap discovery and parsing
├── link_extractor.py       # Link extraction logic
├── utils.py                # Utility functions
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── crawler_data.db        # SQLite database (created on first run)
├── logs/                  # Log files
│   ├── crawler.log       # General logs
│   └── errors.log        # Error logs
└── exports/              # Exported data files
```

## 🐛 Troubleshooting

### Database Locked Error
- Close any database browsers
- Restart the application

### Playwright Installation Issues
```bash
# On Windows
playwright install chromium

# On Linux
playwright install --with-deps chromium
```

### Memory Issues with Large Crawls
- Reduce concurrent threads
- Process sites in smaller batches
- Increase available system RAM

### Rate Limiting / 429 Errors
- Reduce thread count
- System automatically applies delays
- Add custom delays in config

## 📝 Best Practices

1. **Start Small**: Test with 1-2 sites before bulk crawling
2. **Thread Count**: Start with 20 threads, adjust based on results
3. **Regular Exports**: Export data regularly to avoid data loss
4. **Monitor Logs**: Check logs/ directory for errors
5. **Incremental Crawls**: Use re-crawl feature for updates

## 🔒 Data Privacy

- All data stored locally in SQLite database
- No external data transmission except to crawled websites
- Respects robots.txt when checking sitemaps
- User-controlled excluded domains list

## 📈 Performance Tips

### For Maximum Speed
- Use default async mode (no Playwright)
- Increase threads to 50-100 for large sites
- Process multiple sites simultaneously
- Use SSD for database storage

### For Accuracy
- Enable Playwright for JavaScript sites
- Reduce threads to 10-20
- Single site mode
- Review error logs regularly

## 🤝 Support

For issues or questions:
- Check logs in `logs/` directory
- Review error_logs table in database
- Adjust settings in config.py

## 📜 License

This project is provided as-is for personal and commercial use.

## 🔄 Updates & Maintenance

### Regular Maintenance
- Clear old logs periodically
- Backup database regularly
- Update excluded domains list
- Review and optimize sitemap patterns

### Database Backup
```bash
# Copy database file
copy crawler_data.db crawler_data_backup.db
```

## 🎓 Technical Details

### Technologies Used
- **Streamlit**: Web interface
- **aiohttp**: Async HTTP requests
- **BeautifulSoup4**: HTML parsing
- **Playwright**: Browser automation
- **SQLite**: Data storage
- **pandas**: Data export
- **asyncio**: Concurrent operations

### Async Architecture
- Fully async crawling using asyncio
- Semaphore-based concurrency control
- Graceful error handling with retries
- Progress tracking with callbacks

---

**Built with ❤️ for efficient web crawling and backlink analysis**
