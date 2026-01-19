"""
Standalone Playwright fetcher - runs in separate process
Usage: python playwright_fetcher.py <url> [--headless]
"""
import sys
from playwright.sync_api import sync_playwright

def fetch_url(url: str, headless: bool = True):
    """Fetch URL using Playwright in visual or headless mode"""
    try:
        with sync_playwright() as p:
            # Launch browser (headless or visible)
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            # Navigate to URL
            response = page.goto(url, timeout=30000, wait_until='domcontentloaded')
            
            if response and response.status == 200:
                # Get page content
                content = page.content()
                # Print to stdout (Streamlit will capture this)
                print(content)
                browser.close()
                sys.exit(0)
            else:
                status = response.status if response else 'unknown'
                print(f"ERROR: Status {status}", file=sys.stderr)
                browser.close()
                sys.exit(1)
                
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python playwright_fetcher.py <url> [--headless]", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    headless = "--headless" in sys.argv or "-h" in sys.argv
    
    fetch_url(url, headless)
