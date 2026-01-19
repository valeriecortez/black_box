"""
Utility functions for the Web Crawler Application
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Dict
import json
import pandas as pd
from pathlib import Path
from .config import LOG_FILE, ERROR_LOG_FILE, EXPORT_DIR


def setup_logging():
    """Configure logging for the application"""
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler for general logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # File handler for errors
    error_handler = logging.FileHandler(ERROR_LOG_FILE)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from libraries
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def run_async(coro):
    """
    Run an async coroutine in a synchronous context
    Handles event loop creation and cleanup
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    if not timestamp:
        return 'Never'
    
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


def format_number(number: int) -> str:
    """Format large numbers with commas"""
    return f"{number:,}" if number else "0"


def validate_url(url: str) -> bool:
    """Validate URL format"""
    import validators
    return validators.url(url) or validators.domain(url)


def normalize_domain(url: str) -> str:
    """Extract and normalize domain from URL"""
    from urllib.parse import urlparse
    
    if not url.startswith('http'):
        url = 'https://' + url
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    domain = domain.replace('www.', '')
    
    return domain


def export_to_csv(data: List[Dict], filename: str) -> str:
    """Export data to CSV file"""
    filepath = EXPORT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    return str(filepath)


def export_to_excel(data: List[Dict], filename: str, sheet_name: str = 'Sheet1') -> str:
    """Export data to Excel file"""
    filepath = EXPORT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False, sheet_name=sheet_name)
    return str(filepath)


def export_to_json(data: List[Dict], filename: str) -> str:
    """Export data to JSON file"""
    filepath = EXPORT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return str(filepath)


def export_multiple_sheets(sheets_data: Dict[str, List[Dict]], filename: str) -> str:
    """
    Export multiple sheets to Excel file
    
    Args:
        sheets_data: Dict mapping sheet name to data list
        filename: Base filename
    
    Returns:
        Path to created file
    """
    filepath = EXPORT_DIR / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, data in sheets_data.items():
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return str(filepath)


def calculate_crawl_stats(results: Dict[str, Dict]) -> Dict:
    """Calculate statistics from crawl results"""
    stats = {
        'total_processed': len(results),
        'successful': 0,
        'failed': 0,
        'total_links_found': 0,
        'average_links_per_page': 0
    }
    
    for result in results.values():
        if result['status'] == 'success':
            stats['successful'] += 1
            stats['total_links_found'] += result.get('total_links', 0)
        else:
            stats['failed'] += 1
    
    if stats['successful'] > 0:
        stats['average_links_per_page'] = stats['total_links_found'] / stats['successful']
    
    return stats


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to max length with ellipsis"""
    if not text:
        return ''
    
    text = str(text)
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + '...'


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return url


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    return filename[:200]


class ProgressTracker:
    """Track progress of async operations"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.current += increment
    
    def get_percentage(self) -> float:
        """Get completion percentage"""
        if self.total == 0:
            return 0
        return (self.current / self.total) * 100
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_eta(self) -> float:
        """Estimate time remaining in seconds"""
        if self.current == 0:
            return 0
        
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed
        remaining = self.total - self.current
        
        return remaining / rate if rate > 0 else 0
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            'current': self.current,
            'total': self.total,
            'percentage': self.get_percentage(),
            'elapsed': self.get_elapsed_time(),
            'eta': self.get_eta()
        }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


async def async_progress_callback(current: int, total: int, item: str = None):
    """Example async progress callback"""
    percentage = (current / total) * 100
    message = f"Progress: {current}/{total} ({percentage:.1f}%)"
    if item:
        message += f" - {item}"
    
    logging.info(message)
