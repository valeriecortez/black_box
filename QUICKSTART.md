# 🚀 Quick Start Guide

## Installation (First Time Only)

### Windows
1. Open Command Prompt or PowerShell
2. Navigate to the project folder:
   ```
   cd "j:\new testing scripts"
   ```
3. Run setup:
   ```
   setup.bat
   ```

### Linux/Mac
1. Open Terminal
2. Navigate to the project folder
3. Make scripts executable:
   ```bash
   chmod +x run.sh setup.sh
   ```
4. Run setup:
   ```bash
   ./setup.sh
   ```

## Running the Application

### Windows
Double-click `run.bat` or run in Command Prompt:
```
run.bat
```

### Linux/Mac
```bash
./run.sh
```

Or use Python directly:
```bash
streamlit run app.py
```

## First Steps

### 1️⃣ Add Your First Site
- Open the app (should open automatically in browser)
- Go to **"🌐 Manage Sites"**
- Enter a website URL (e.g., `example.com`)
- Click **"Add Site"**

### 2️⃣ Discover Sitemap
- Go to **"🗺️ Sitemap Crawler"**
- Select your site
- Click **"🚀 Start Crawl"**
- Wait for sitemap discovery and URL extraction

### 3️⃣ Extract Outgoing Links
- Go to **"🔗 Link Extractor"**
- Select your site
- Adjust threads (20 is default, recommended)
- Click **"🚀 Start Link Extraction"**
- Monitor progress in real-time

### 4️⃣ Export Results
- Go to **"📥 Export Data"**
- Select "Outgoing Links"
- Choose format (Excel recommended)
- Click **"📤 Export"**
- Download your data!

## Common Tasks

### Adding Excluded Domains
Go to **"⚙️ Settings"** → **"🚫 Excluded Domains"**
- Add domains like: `facebook.com`, `twitter.com`
- These will be filtered out from outgoing links

### Batch Processing Multiple Sites
1. Add all sites in **"Manage Sites"**
2. Go to **"Sitemap Crawler"**
3. Select **"Multiple Sites"** mode
4. Check the sites you want to crawl
5. Click **"Start Batch Crawl"**

### Re-crawling for Updates
1. Go to **"Sitemap Crawler"**
2. Select a previously crawled site
3. Click **"Start Crawl"** again
4. System will detect only new/updated posts
5. Go to **"Link Extractor"** to process new posts

## Performance Tips

### For Speed (100+ posts)
- Increase threads to **50-100**
- Use **Silent Mode** (default)
- Process one site at a time
- Good internet connection required

### For Accuracy (JavaScript sites)
- Enable **Playwright** in Link Extractor
- Reduce threads to **10-20**
- Expect slower processing
- Better for dynamic content

### For Large Scale (1000+ posts)
- Process in batches (500-1000 at a time)
- Export data after each batch
- Monitor system resources
- Use powerful machine (8GB+ RAM)

## Troubleshooting

### "Database is locked"
- Close any SQLite browsers
- Restart the application

### "No sitemap found"
- Enter custom sitemap URL when adding site
- Check if website has sitemap
- Some sites don't have sitemaps

### Slow extraction
- Reduce thread count
- Check your internet speed
- Some sites have rate limiting

### Memory issues
- Reduce threads to 10-20
- Process fewer posts at once
- Close other applications

## File Locations

- **Database**: `crawler_data.db`
- **Logs**: `logs/` folder
- **Exports**: `exports/` folder
- **Settings**: `config.py`

## Next Steps

Once comfortable with basics:

1. **Customize Settings**
   - Add your commonly crawled site patterns
   - Set up excluded domains list
   - Adjust default thread counts

2. **Monitor & Maintain**
   - Check logs regularly
   - Export data periodically
   - Clear old logs monthly

3. **Advanced Features**
   - Use filters for specific link types
   - Export unique links only
   - Analyze link positions

## Getting Help

Check these in order:
1. **Logs**: `logs/crawler.log` and `logs/errors.log`
2. **README.md**: Full documentation
3. **Database**: Review error_logs table
4. **Config**: Check `config.py` settings

## Example Workflow

```
1. Add 10 sites → Manage Sites
2. Crawl all sitemaps → Sitemap Crawler (Multiple Sites mode)
3. Review discovered posts → Dashboard
4. Extract links (20 threads) → Link Extractor
5. Export to Excel → Export Data
6. Analyze in Excel/Google Sheets
```

---

**Happy Crawling! 🎉**
