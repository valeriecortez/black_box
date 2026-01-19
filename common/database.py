"""
Database operations for the Web Crawler Application
Handles all database interactions using SQLite with async support
"""
import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from .config import DB_PATH
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                sitemap_url TEXT,
                status TEXT DEFAULT 'pending',
                total_posts INTEGER DEFAULT 0,
                total_outgoing_links INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_crawled_at TIMESTAMP,
                last_updated_at TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Sitemap URLs table (for sites with multiple sitemaps)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sitemap_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                sitemap_url TEXT NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                total_urls INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE,
                UNIQUE(site_id, sitemap_url)
            )
        ''')
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'pending',
                outgoing_links_count INTEGER DEFAULT 0,
                crawled_at TIMESTAMP,
                screenshot_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE
            )
        ''')
        
        # Check for missing columns (for existing databases)
        cursor.execute("PRAGMA table_info(posts)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'screenshot_path' not in columns:
            cursor.execute("ALTER TABLE posts ADD COLUMN screenshot_path TEXT")

        # Outgoing links table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outgoing_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                site_id INTEGER NOT NULL,
                target_url TEXT NOT NULL,
                anchor_text TEXT,
                position_paragraph INTEGER,
                position_word INTEGER,
                link_location TEXT,
                rel_attributes TEXT,
                target_attribute TEXT,
                is_article_link BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE
            )
        ''')
        
        # Crawl history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawl_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER NOT NULL,
                crawl_type TEXT NOT NULL,
                status TEXT NOT NULL,
                new_posts_found INTEGER DEFAULT 0,
                new_links_found INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE
            )
        ''')
        
        # Error logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_id INTEGER,
                post_url TEXT,
                error_type TEXT NOT NULL,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Excluded domains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS excluded_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Custom sitemap URLs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS custom_sitemaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Custom post patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_site_id ON posts(site_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_url ON posts(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outgoing_links_post_id ON outgoing_links(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outgoing_links_site_id ON outgoing_links(site_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outgoing_links_target_url ON outgoing_links(target_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crawl_history_site_id ON crawl_history(site_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_logs_site_id ON error_logs(site_id)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    # ============ Site Operations ============
    
    async def add_site(self, url: str, sitemap_url: str = None, notes: str = None) -> int:
        """Add a new site to the database"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    'INSERT INTO sites (url, sitemap_url, notes) VALUES (?, ?, ?)',
                    (url, sitemap_url, notes)
                )
                await db.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Site already exists, return its ID
                cursor = await db.execute('SELECT id FROM sites WHERE url = ?', (url,))
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def get_site(self, site_id: int) -> Optional[Dict]:
        """Get site details by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_sites(self) -> List[Dict]:
        """Get all sites"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute('SELECT * FROM sites ORDER BY created_at DESC')
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_site(self, site_id: int, **kwargs):
        """Update site information"""
        allowed_fields = ['url', 'sitemap_url', 'status', 'total_posts', 
                         'total_outgoing_links', 'last_crawled_at', 'notes']
        
        updates = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return
        
        values.append(datetime.now())
        values.append(site_id)
        
        query = f"UPDATE sites SET {', '.join(updates)}, last_updated_at = ? WHERE id = ?"
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, values)
            await db.commit()
    
    async def delete_site(self, site_id: int):
        """Delete a site and all its associated data"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM sites WHERE id = ?', (site_id,))
            await db.commit()
    
    # ============ Sitemap Operations ============
    
    async def add_sitemap_url(self, site_id: int, sitemap_url: str, 
                             is_primary: bool = False, total_urls: int = 0):
        """Add a sitemap URL for a site"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT OR IGNORE INTO sitemap_urls 
                   (site_id, sitemap_url, is_primary, total_urls) 
                   VALUES (?, ?, ?, ?)''',
                (site_id, sitemap_url, is_primary, total_urls)
            )
            await db.commit()
    
    async def get_site_sitemaps(self, site_id: int) -> List[Dict]:
        """Get all sitemap URLs for a site"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                'SELECT * FROM sitemap_urls WHERE site_id = ?',
                (site_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============ Post Operations ============
    
    async def add_post(self, site_id: int, url: str, title: str = None) -> int:
        """Add a new post"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    'INSERT INTO posts (site_id, url, title) VALUES (?, ?, ?)',
                    (site_id, url, title)
                )
                await db.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Post already exists, return its ID
                cursor = await db.execute('SELECT id FROM posts WHERE url = ?', (url,))
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def get_posts_by_site(self, site_id: int, status: str = None) -> List[Dict]:
        """Get all posts for a site"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            if status:
                cursor = await db.execute(
                    'SELECT * FROM posts WHERE site_id = ? AND status = ?',
                    (site_id, status)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM posts WHERE site_id = ?',
                    (site_id,)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def update_post_status(self, post_id: int, status: str, 
                                 outgoing_links_count: int = None,
                                 screenshot_path: str = None):
        """Update post crawl status"""
        async with aiosqlite.connect(self.db_path) as db:
            if outgoing_links_count is not None:
                if screenshot_path:
                    await db.execute(
                        '''UPDATE posts 
                           SET status = ?, outgoing_links_count = ?, crawled_at = ?, screenshot_path = ? 
                           WHERE id = ?''',
                        (status, outgoing_links_count, datetime.now(), screenshot_path, post_id)
                    )
                else:
                    await db.execute(
                        '''UPDATE posts 
                           SET status = ?, outgoing_links_count = ?, crawled_at = ? 
                           WHERE id = ?''',
                        (status, outgoing_links_count, datetime.now(), post_id)
                    )
            else:
                await db.execute(
                    'UPDATE posts SET status = ?, crawled_at = ? WHERE id = ?',
                    (status, datetime.now(), post_id)
                )
            await db.commit()
    
    async def get_uncrawled_posts(self, site_id: int) -> List[Dict]:
        """Get posts that haven't been crawled yet"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                'SELECT * FROM posts WHERE site_id = ? AND status = ?',
                (site_id, 'pending')
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============ Outgoing Links Operations ============
    
    async def add_outgoing_link(self, post_id: int, site_id: int, target_url: str,
                               anchor_text: str = None, position_paragraph: int = None,
                               position_word: int = None, link_location: str = None,
                               rel_attributes: str = None, target_attribute: str = None,
                               is_article_link: bool = True):
        """Add an outgoing link"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT INTO outgoing_links 
                   (post_id, site_id, target_url, anchor_text, position_paragraph, 
                    position_word, link_location, rel_attributes, target_attribute, 
                    is_article_link)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (post_id, site_id, target_url, anchor_text, position_paragraph,
                 position_word, link_location, rel_attributes, target_attribute,
                 is_article_link)
            )
            await db.commit()
    
    async def get_outgoing_links_by_post(self, post_id: int) -> List[Dict]:
        """Get all outgoing links for a post"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            cursor = await db.execute(
                'SELECT * FROM outgoing_links WHERE post_id = ?',
                (post_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_outgoing_links_by_site(self, site_id: int, 
                                        unique_only: bool = False) -> List[Dict]:
        """Get all outgoing links for a site"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            if unique_only:
                cursor = await db.execute(
                    '''SELECT DISTINCT target_url, anchor_text, link_location
                       FROM outgoing_links WHERE site_id = ?''',
                    (site_id,)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM outgoing_links WHERE site_id = ?',
                    (site_id,)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============ Crawl History Operations ============
    
    async def start_crawl(self, site_id: int, crawl_type: str) -> int:
        """Record the start of a crawl operation"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                'INSERT INTO crawl_history (site_id, crawl_type, status) VALUES (?, ?, ?)',
                (site_id, crawl_type, 'running')
            )
            await db.commit()
            return cursor.lastrowid
    
    async def complete_crawl(self, crawl_id: int, status: str = 'completed',
                            new_posts_found: int = 0, new_links_found: int = 0,
                            errors_count: int = 0, error_message: str = None):
        """Mark a crawl as completed"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''UPDATE crawl_history 
                   SET status = ?, new_posts_found = ?, new_links_found = ?, 
                       errors_count = ?, completed_at = ?, error_message = ?
                   WHERE id = ?''',
                (status, new_posts_found, new_links_found, errors_count, 
                 datetime.now(), error_message, crawl_id)
            )
            await db.commit()
    
    async def get_crawl_history(self, site_id: int = None, limit: int = 50) -> List[Dict]:
        """Get crawl history"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            if site_id:
                cursor = await db.execute(
                    '''SELECT * FROM crawl_history WHERE site_id = ? 
                       ORDER BY started_at DESC LIMIT ?''',
                    (site_id, limit)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM crawl_history ORDER BY started_at DESC LIMIT ?',
                    (limit,)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============ Error Logging Operations ============
    
    async def log_error(self, site_id: int, error_type: str, error_message: str,
                       post_url: str = None, retry_count: int = 0):
        """Log an error"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT INTO error_logs 
                   (site_id, post_url, error_type, error_message, retry_count)
                   VALUES (?, ?, ?, ?, ?)''',
                (site_id, post_url, error_type, error_message, retry_count)
            )
            await db.commit()
    
    async def get_errors(self, site_id: int = None, resolved: bool = False) -> List[Dict]:
        """Get error logs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            if site_id:
                cursor = await db.execute(
                    '''SELECT * FROM error_logs 
                       WHERE site_id = ? AND resolved = ?
                       ORDER BY created_at DESC''',
                    (site_id, resolved)
                )
            else:
                cursor = await db.execute(
                    'SELECT * FROM error_logs WHERE resolved = ? ORDER BY created_at DESC',
                    (resolved,)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def get_recent_screenshots(self, limit: int = 4) -> List[Dict]:
        """Get recent posts with screenshots"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            try:
                cursor = await db.execute(
                    '''SELECT p.*, s.url as site_url 
                       FROM posts p
                       JOIN sites s ON p.site_id = s.id 
                       WHERE p.screenshot_path IS NOT NULL 
                       ORDER BY p.crawled_at DESC 
                       LIMIT ?''',
                    (limit,)
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                return []
    
    # ============ Settings Operations ============
    
    async def get_setting(self, key: str, default=None):
        """Get a setting value"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = await cursor.fetchone()
            return row[0] if row else default
    
    async def set_setting(self, key: str, value: str):
        """Set a setting value"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                '''INSERT OR REPLACE INTO settings (key, value, updated_at)
                   VALUES (?, ?, ?)''',
                (key, value, datetime.now())
            )
            await db.commit()
    
    # ============ Excluded Domains Operations ============
    
    async def add_excluded_domain(self, domain: str):
        """Add a domain to exclude list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR IGNORE INTO excluded_domains (domain) VALUES (?)',
                (domain,)
            )
            await db.commit()
    
    async def get_excluded_domains(self) -> List[str]:
        """Get all excluded domains"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT domain FROM excluded_domains')
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def delete_excluded_domain(self, domain: str):
        """Remove a domain from exclude list"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM excluded_domains WHERE domain = ?', (domain,))
            await db.commit()
    
    # ============ Statistics Operations ============
    
    async def get_dashboard_stats(self) -> Dict:
        """Get overall statistics for dashboard"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Total sites
            cursor = await db.execute('SELECT COUNT(*) FROM sites')
            stats['total_sites'] = (await cursor.fetchone())[0]
            
            # Total posts
            cursor = await db.execute('SELECT COUNT(*) FROM posts')
            stats['total_posts'] = (await cursor.fetchone())[0]
            
            # Total outgoing links
            cursor = await db.execute('SELECT COUNT(*) FROM outgoing_links')
            stats['total_outgoing_links'] = (await cursor.fetchone())[0]
            
            # Crawled posts
            cursor = await db.execute('SELECT COUNT(*) FROM posts WHERE status = ?', ('crawled',))
            stats['crawled_posts'] = (await cursor.fetchone())[0]
            
            # Pending posts
            cursor = await db.execute('SELECT COUNT(*) FROM posts WHERE status = ?', ('pending',))
            stats['pending_posts'] = (await cursor.fetchone())[0]
            
            # Active crawls
            cursor = await db.execute('SELECT COUNT(*) FROM crawl_history WHERE status = ?', ('running',))
            stats['active_crawls'] = (await cursor.fetchone())[0]
            
            # Recent errors
            cursor = await db.execute('SELECT COUNT(*) FROM error_logs WHERE resolved = 0')
            stats['unresolved_errors'] = (await cursor.fetchone())[0]
            
            return stats
