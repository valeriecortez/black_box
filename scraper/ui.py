"""
Advanced Web Crawler & Backlink Analyzer
Main Streamlit Application
"""
import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd
from pathlib import Path

# Import modules
from common.database import DatabaseManager
from .sitemap_crawler import SitemapCrawler, discover_multiple_sites
from .link_extractor import extract_from_multiple_pages, batch_extract_with_fallback
from common.utils import (
    setup_logging, run_async, format_timestamp, format_number,
    validate_url, export_to_csv, export_to_excel, export_to_json,
    export_multiple_sheets, truncate_text, ProgressTracker
)
from common.config import (
    PAGE_TITLE, PAGE_ICON, LAYOUT, COLORS, DEFAULT_THREADS,
    DEFAULT_EXCLUDED_DOMAINS, POST_URL_PATTERNS, EXCLUDE_URL_PATTERNS
)

# Initialize logging
setup_logging()

# Page configuration moved to main app
# st.set_page_config(...)

# Styles are applied in the main app
# st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

# Session state initialization
if 'crawl_running' not in st.session_state:
    st.session_state.crawl_running = False

if 'current_operation' not in st.session_state:
    st.session_state.current_operation = None


def render_scraper_ui():
    """Main Scraper Interface"""
    
    if "navigation_page" not in st.session_state:
        st.session_state.navigation_page = "📊 Dashboard"
    
    # Sidebar navigation
    st.sidebar.title("🔍 Navigation")
    
    # Define pages
    pages_list = ["📊 Dashboard", "🌐 Manage Sites", "🗺️ Sitemap Crawler", 
                 "🔗 Link Extractor", "📥 Export Data", "⚙️ Settings"]
    
    # Check if we need to switch page from external action
    if "switch_to_page" in st.session_state:
        try:
            target_index = pages_list.index(st.session_state.switch_to_page)
            # We can't easily set the index of the radio if it's already rendered or if we want to rely on the key.
            # Best way is to rely on 'key' param which syncs with session_state.
            st.session_state.navigation_page = st.session_state.switch_to_page
            del st.session_state.switch_to_page
        except ValueError:
            pass
            
    # Sync nav_radio with navigation_page
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = st.session_state.navigation_page
    
    # If navigation_page was updated programmatically separate from the widget, force update
    if st.session_state.navigation_page != st.session_state.nav_radio:
        st.session_state.nav_radio = st.session_state.navigation_page

    def update_navigation_state():
        st.session_state.navigation_page = st.session_state.nav_radio

    page = st.sidebar.radio(
        "Go to",
        pages_list,
        key="nav_radio",
        on_change=update_navigation_state
    )
    
    # Route to appropriate page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "🌐 Manage Sites":
        show_manage_sites()
    elif page == "🗺️ Sitemap Crawler":
        show_sitemap_crawler()
    elif page == "🔗 Link Extractor":
        show_link_extractor()
    elif page == "📥 Export Data":
        show_export_data()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Display dashboard with statistics"""
    st.title("📊 Dashboard")
    
    # Get statistics
    stats = run_async(db.get_dashboard_stats())
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Sites", format_number(stats['total_sites']))
    
    with col2:
        st.metric("Total Posts", format_number(stats['total_posts']))
    
    with col3:
        st.metric("Outgoing Links", format_number(stats['total_outgoing_links']))
    
    with col4:
        st.metric("Active Crawls", format_number(stats['active_crawls']))
    
    st.divider()
    
    # Progress metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Crawled Posts", format_number(stats['crawled_posts']))
    
    with col2:
        st.metric("Pending Posts", format_number(stats['pending_posts']))
    
    # Show screenshots
    st.subheader("📸 Recent Captures")
    screenshots = run_async(db.get_recent_screenshots(limit=4))
    if screenshots:
        cols = st.columns(4)
        for i, post in enumerate(screenshots):
            with cols[i]:
                try:
                    st.image(post['screenshot_path'], caption=truncate_text(post['title'] or post['url'], 30), use_column_width=True)
                except Exception:
                    st.warning("Image missing")
    else:
        st.info("No screenshots available. Enable 'Take Screenshots' in Link Extractor.")

    # Show recent sites
    st.subheader("📝 Recent Sites")
    sites = run_async(db.get_all_sites())
    
    if sites:
        # Convert to DataFrame
        df = pd.DataFrame(sites)
        df = df[['url', 'status', 'total_posts', 'total_outgoing_links', 'last_crawled_at']]
        df.columns = ['Site URL', 'Status', 'Posts', 'Outgoing Links', 'Last Crawled']
        df['Last Crawled'] = df['Last Crawled'].apply(format_timestamp)
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sites added yet. Go to 'Manage Sites' to add your first site.")
    
    # Show crawl history
    st.subheader("📜 Recent Crawl History")
    history = run_async(db.get_crawl_history(limit=10))
    
    if history:
        df_history = pd.DataFrame(history)
        
        # Dashboard Charts
        st.subheader("📈 Activity Trends")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Posts & Links Chart
            chart_data = df_history[['new_posts_found', 'new_links_found', 'started_at']].copy()
            chart_data['started_at'] = pd.to_datetime(chart_data['started_at'])
            chart_data.set_index('started_at', inplace=True)
            st.caption("New Content Discovery")
            st.bar_chart(chart_data)
            
        with chart_col2:
            # Crawl Status Distribution
            status_counts = df_history['status'].value_counts()
            st.caption("Crawl Status")
            st.bar_chart(status_counts)

        df_history = df_history[['crawl_type', 'status', 'new_posts_found', 'new_links_found', 'started_at']]
        df_history.columns = ['Type', 'Status', 'New Posts', 'New Links', 'Started At']
        df_history['Started At'] = df_history['Started At'].apply(format_timestamp)
        
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("No crawl history yet.")
    
    # Show unresolved errors
    errors = run_async(db.get_errors(resolved=False))
    if errors:
        st.warning(f"⚠️ {len(errors)} unresolved error(s) found. Check the logs for details.")


def show_manage_sites():
    """Manage sites interface"""
    st.title("🌐 Manage Sites")
    
    # Add new site section
    st.subheader("➕ Add New Site")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_site_url = st.text_input(
            "Site URL",
            placeholder="https://example.com or example.com",
            help="Enter the website URL (with or without https://)"
        )
    
    with col2:
        notes = st.text_input("Notes (optional)")
    
    custom_sitemap = st.text_input(
        "Custom Sitemap URL (optional)",
        placeholder="https://example.com/sitemap.xml"
    )
    
    if st.button("Add Site", type="primary"):
        if new_site_url:
            if validate_url(new_site_url):
                site_id = run_async(db.add_site(new_site_url, custom_sitemap, notes))
                if site_id:
                    st.success(f"✅ Site added successfully! Site ID: {site_id}")
                else:
                    st.info("ℹ️ Site already exists in the database.")
            else:
                st.error("❌ Invalid URL format. Please enter a valid URL.")
        else:
            st.error("❌ Please enter a site URL.")
    
    st.divider()
    
    # List existing sites
    st.subheader("📋 Existing Sites")
    
    sites = run_async(db.get_all_sites())
    
    if sites:
        for site in sites:
            with st.expander(f"🌐 {site['url']} - {site['status']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Site ID:** {site['id']}")
                    st.write(f"**Status:** {site['status']}")
                    st.write(f"**Sitemap:** {site['sitemap_url'] or 'Not discovered'}")
                
                with col2:
                    st.write(f"**Total Posts:** {format_number(site['total_posts'])}")
                    st.write(f"**Outgoing Links:** {format_number(site['total_outgoing_links'])}")
                    st.write(f"**Created:** {format_timestamp(site['created_at'])}")
                
                with col3:
                    st.write(f"**Last Crawled:** {format_timestamp(site['last_crawled_at'])}")
                    st.write(f"**Notes:** {site['notes'] or 'None'}")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(f"🗺️ Crawl Sitemap", key=f"sitemap_{site['id']}"):
                        st.session_state.selected_site_id = site['id']
                        st.session_state.navigation_page = "🗺️ Sitemap Crawler"
                        st.rerun()
                
                with col2:
                    if st.button(f"🔗 Extract Links", key=f"links_{site['id']}"):
                        st.session_state.selected_site_id = site['id']
                        st.session_state.navigation_page = "🔗 Link Extractor"
                        st.rerun()
                
                with col3:
                    if st.button(f"🗑️ Delete", key=f"delete_{site['id']}"):
                        if st.session_state.get(f"confirm_delete_{site['id']}", False):
                            run_async(db.delete_site(site['id']))
                            st.success("Site deleted!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{site['id']}"] = True
                            st.warning("Click again to confirm deletion")
    else:
        st.info("No sites added yet. Add your first site above.")


def show_sitemap_crawler():
    """Sitemap crawler interface"""
    st.title("🗺️ Sitemap Crawler")
    
    # Get all sites
    sites = run_async(db.get_all_sites())
    
    if not sites:
        st.warning("No sites available. Please add sites first in 'Manage Sites'.")
        return
    
    st.subheader("Crawl Site Sitemaps")
    
    # Crawl mode selection
    crawl_mode = st.radio(
        "Crawl Mode",
        ["Single Site", "Multiple Sites"],
        horizontal=True
    )
    
    if crawl_mode == "Single Site":
        # Single site crawl
        site_options = {f"{site['url']} (ID: {site['id']})": site['id'] for site in sites}
        selected_site_key = st.selectbox("Select Site", list(site_options.keys()))
        selected_site_id = site_options[selected_site_key]
        
        selected_site = run_async(db.get_site(selected_site_id))
        
        # Show site info
        st.info(f"**Current Sitemap:** {selected_site['sitemap_url'] or 'Not discovered yet'}")
        
        # Crawl options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            use_custom = st.checkbox("Use custom sitemap URL")
            custom_sitemap_url = None
            if use_custom:
                custom_sitemap_url = st.text_input("Custom Sitemap URL", placeholder="https://example.com/sitemap.xml")
        
        with col2:
            use_browser = st.checkbox(
                "🌐 Browser Mode",
                help="Use real Chrome browser to bypass SSL/firewall issues. Runs in separate process."
            )
            if use_browser:
                st.caption("✅ Browser enabled")
        
        # Manual XML paste option in expandable section
        with st.expander("📋 Manual XML Paste (Alternative)"):
            st.markdown("If browser mode fails, paste sitemap XML content here:")
            manual_xml = st.text_area(
                "Paste sitemap XML content",
                height=150,
                placeholder="Open sitemap URL in browser, copy all XML, paste here...",
                help="Bypass all connection issues by manually pasting the XML"
            )
        
        if st.button("🚀 Start Crawl", type="primary"):
            with st.spinner("Crawling sitemap..." + (" (Browser mode)" if use_browser else "")):
                # Start crawl history
                crawl_id = run_async(db.start_crawl(selected_site_id, 'sitemap'))
                
                async def crawl_sitemap_async():
                    async with SitemapCrawler(use_browser=use_browser) as crawler:
                        result = await crawler.crawl_site_sitemap(
                            selected_site['url'],
                            custom_sitemap=custom_sitemap_url,
                            manual_xml=manual_xml if manual_xml.strip() else None
                        )
                        return result
                
                result = run_async(crawl_sitemap_async())
                
                if result['status'] == 'success':
                    # Update site with sitemap URL
                    run_async(db.update_site(
                        selected_site_id,
                        sitemap_url=result['sitemap_url'],
                        total_posts=result['total_urls'],
                        status='sitemap_crawled'
                    ))
                    
                    # Add sitemap URL to database
                    run_async(db.add_sitemap_url(
                        selected_site_id,
                        result['sitemap_url'],
                        is_primary=True,
                        total_urls=result['total_urls']
                    ))
                    
                    # Add posts to database
                    for url in result['urls']:
                        run_async(db.add_post(selected_site_id, url))
                    
                    # Complete crawl history
                    run_async(db.complete_crawl(
                        crawl_id,
                        status='completed',
                        new_posts_found=result['total_urls']
                    ))
                    
                    st.success(f"✅ {result['message']}")
                    st.info(f"**Sitemap URL:** {result['sitemap_url']}")
                    st.info(f"**Total Posts Found:** {format_number(result['total_urls'])}")
                    
                elif result['status'] == 'no_sitemap':
                    run_async(db.complete_crawl(crawl_id, status='no_sitemap'))
                    st.warning(result['message'])
                    
                else:
                    run_async(db.complete_crawl(
                        crawl_id,
                        status='error',
                        error_message=result['message']
                    ))
                    run_async(db.log_error(
                        selected_site_id,
                        'sitemap_crawl',
                        result['message']
                    ))
                    st.error(f"❌ {result['message']}")
    
    else:
        # Multiple sites crawl
        st.write("Select sites to crawl:")
        
        selected_sites = []
        for site in sites:
            if st.checkbox(f"{site['url']}", key=f"multi_{site['id']}"):
                selected_sites.append(site)
        
        concurrent_sites = st.slider(
            "Concurrent Sites",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of sites to crawl simultaneously"
        )
        
        if st.button("🚀 Start Batch Crawl", type="primary"):
            if not selected_sites:
                st.error("Please select at least one site")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                async def batch_crawl():
                    site_urls = [site['url'] for site in selected_sites]
                    results = await discover_multiple_sites(site_urls, concurrent_sites)
                    return results
                
                results = run_async(batch_crawl())
                
                # Process results
                success_count = 0
                for site in selected_sites:
                    result = results.get(site['url'])
                    if result and result['status'] == 'success':
                        # Update database
                        run_async(db.update_site(
                            site['id'],
                            sitemap_url=result['sitemap_url'],
                            total_posts=result['total_urls']
                        ))
                        
                        # Add posts
                        for url in result['urls']:
                            run_async(db.add_post(site['id'], url))
                        
                        success_count += 1
                
                progress_bar.progress(1.0)
                st.success(f"✅ Successfully crawled {success_count}/{len(selected_sites)} sites")


def show_link_extractor():
    """Link extraction interface"""
    st.title("🔗 Link Extractor")
    
    # Get all sites
    sites = run_async(db.get_all_sites())
    
    if not sites:
        st.warning("No sites available. Please add sites first in 'Manage Sites'.")
        return
    
    st.subheader("Extract Outgoing Links")
    
    # Site selection
    site_options = {f"{site['url']} (ID: {site['id']})": site['id'] for site in sites}
    selected_site_key = st.selectbox("Select Site", list(site_options.keys()))
    selected_site_id = site_options[selected_site_key]
    
    selected_site = run_async(db.get_site(selected_site_id))
    
    # Show site stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Posts", format_number(selected_site['total_posts']))
    with col2:
        pending_posts = len(run_async(db.get_uncrawled_posts(selected_site_id)))
        st.metric("Pending Posts", format_number(pending_posts))
    with col3:
        st.metric("Total Links", format_number(selected_site['total_outgoing_links']))
    
    st.divider()
    
    # Settings
    col1, col2 = st.columns(2)
    
    with col1:
        threads = st.slider(
            "Concurrent Threads",
            min_value=1,
            max_value=100,
            value=DEFAULT_THREADS,
            help="Number of URLs to process simultaneously"
        )
    
    with col2:
        use_playwright = st.checkbox(
            "Enable Playwright (for JavaScript sites)",
            help="Use browser automation for JavaScript-heavy sites (slower)"
        )
        
        take_screenshots = False
        if use_playwright:
            take_screenshots = st.checkbox(
                "📸 Take screenshots of pages",
                help="Capture full-page screenshot of each post (Slows down process, fills disk space)"
            )
    
    # Limit number of posts to extract
    col1, col2 = st.columns([1, 1])
    
    with col1:
        crawl_all = st.checkbox("Crawl all posts", value=False)
    
    with col2:
        if not crawl_all:
            max_posts = st.number_input(
                "Number of posts to extract",
                min_value=1,
                max_value=100000,
                value=100,
                step=10,
                help="How many posts to extract links from"
            )
        else:
            max_posts = None
            st.info(f"{pending_posts} posts will be processed")
    
    if st.button("🚀 Start Link Extraction", type="primary"):
        # Get posts to crawl
        posts = run_async(db.get_uncrawled_posts(selected_site_id))
        
        if not posts:
            st.info("No pending posts to crawl. All posts have been processed!")
            return
        
        if max_posts:
            posts = posts[:max_posts]
        
        post_urls = [post['url'] for post in posts]
        
        st.info(f"Starting extraction for {len(post_urls)} posts...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_container = st.empty()
        
        # Get excluded domains
        excluded_domains = run_async(db.get_excluded_domains())
        
        # Start crawl
        crawl_id = run_async(db.start_crawl(selected_site_id, 'link_extraction'))
        
        total_links_found = 0
        processed = 0
        posts_dict = {post['url']: post for post in posts}
        
        async def progress_callback(current, total, url):
            nonlocal processed
            processed = current
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"Processing: {truncate_text(url, 80)} ({current}/{total})")
        
        async def extract_and_save_links():
            """Extract links and save to database simultaneously"""
            nonlocal total_links_found
            
            new_links = 0
            errors = 0
            
            if use_playwright:
                extractor_func = extract_from_multiple_pages
                args = (post_urls, excluded_domains, threads, True, None)
            else:
                extractor_func = batch_extract_with_fallback
                args = (post_urls, excluded_domains, threads, None)
            
            # Create async generator for results
            from link_extractor import LinkExtractor
            import asyncio
            
            async with LinkExtractor(use_playwright=use_playwright) as extractor:
                semaphore = asyncio.Semaphore(threads)
                completed = 0
                
                async def extract_and_save_single(post_url: str):
                    nonlocal completed, new_links, errors, total_links_found
                    
                    async with semaphore:
                        post = posts_dict.get(post_url)
                        if not post:
                            return
                        
                        # Prepare screenshot path if enabled
                        screenshot_file = None
                        if take_screenshots:
                            try:
                                # Create directory structure: exports/screenshots/{site_id}
                                screenshots_dir = Path("exports/screenshots") / str(selected_site_id)
                                screenshots_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Filename: post_id.png
                                filename = f"{post['id']}.png"
                                screenshot_file = str(screenshots_dir / filename)
                            except Exception as e:
                                print(f"Error preparing screenshot path: {e}")
                                screenshot_file = None
                        
                        # Extract links
                        result = await extractor.extract_outgoing_links(post_url, excluded_domains, screenshot_path=screenshot_file)
                        
                        # Save immediately to database
                        if result and result['status'] == 'success':
                            # Update post status with screenshot path
                            await db.update_post_status(
                                post['id'],
                                'crawled',
                                result['total_links'],
                                screenshot_path=screenshot_file
                            )
                            
                            # Save links one by one
                            for link in result['links']:
                                await db.add_outgoing_link(
                                    post['id'],
                                    selected_site_id,
                                    link['url'],
                                    link.get('anchor_text'),
                                    link.get('position_paragraph'),
                                    link.get('position_word'),
                                    link.get('link_location'),
                                    link.get('rel_attributes'),
                                    link.get('target'),
                                    link.get('is_article_link', True)
                                )
                                new_links += 1
                                total_links_found += 1
                        else:
                            # Log error immediately
                            error_msg = result.get('message', 'Unknown error') if result else 'No result'
                            await db.log_error(
                                selected_site_id,
                                'link_extraction',
                                error_msg,
                                post_url
                            )
                            errors += 1
                        
                        # Update progress
                        completed += 1
                        await progress_callback(completed, len(post_urls), post_url)
                
                # Process all posts
                tasks = [extract_and_save_single(url) for url in post_urls]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            return new_links, errors
        
        new_links, errors = run_async(extract_and_save_links())
        
        # Update site stats
        run_async(db.update_site(
            selected_site_id,
            total_outgoing_links=selected_site['total_outgoing_links'] + new_links,
            last_crawled_at=datetime.now().isoformat()
        ))
        
        # Complete crawl
        run_async(db.complete_crawl(
            crawl_id,
            status='completed',
            new_links_found=new_links,
            errors_count=errors
        ))
        
        progress_bar.progress(1.0)
        status_text.empty()
        
        st.success(f"✅ Extraction completed! Data saved continuously during crawl.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Posts Processed", format_number(len(post_urls)))
        with col2:
            st.metric("New Links Found", format_number(new_links))
        with col3:
            st.metric("Errors", errors)
        
        if errors > 0:
            st.warning(f"⚠️ {errors} error(s) occurred during extraction. Check error logs for details.")
        
        # Show sample of extracted links
        if new_links > 0:
            st.divider()
            st.subheader("Sample of Extracted Links")
            recent_links = run_async(db.get_outgoing_links_by_site(selected_site_id))
            if recent_links:
                sample_df = pd.DataFrame(recent_links[:10])
                if not sample_df.empty:
                    display_cols = ['target_url', 'anchor_text', 'link_location', 'is_article_link']
                    display_cols = [col for col in display_cols if col in sample_df.columns]
                    st.dataframe(sample_df[display_cols], use_container_width=True)
                errors += 1
        
        # Update site stats
        run_async(db.update_site(
            selected_site_id,
            total_outgoing_links=selected_site['total_outgoing_links'] + new_links,
            last_crawled_at=datetime.now().isoformat()
        ))
        
        # Complete crawl
        run_async(db.complete_crawl(
            crawl_id,
            status='completed',
            new_links_found=new_links,
            errors_count=errors
        ))
        
        progress_bar.progress(1.0)
        st.success(f"✅ Extraction completed!")
        st.info(f"**Posts Processed:** {len(post_urls)}")
        st.info(f"**New Links Found:** {format_number(new_links)}")
        
        if errors > 0:
            st.warning(f"⚠️ {errors} error(s) occurred during extraction")


def show_export_data():
    """Export data interface"""
    st.title("📥 Export Data")
    
    # Get all sites
    sites = run_async(db.get_all_sites())
    
    if not sites:
        st.warning("No data available to export.")
        return
    
    st.subheader("Export Options")
    
    # Select export type
    export_type = st.radio(
        "What to export?",
        ["Outgoing Links", "Sites Summary", "Posts List", "Complete Report"],
        horizontal=True
    )
    
    # Site selection
    site_options = {f"{site['url']} (ID: {site['id']})": site['id'] for site in sites}
    site_options["All Sites"] = None
    
    selected_site_key = st.selectbox("Select Site", list(site_options.keys()))
    selected_site_id = site_options[selected_site_key]
    
    # Format selection
    export_format = st.radio(
        "Export Format",
        ["CSV", "Excel", "JSON"],
        horizontal=True
    )
    
    # Unique links option (for outgoing links)
    if export_type == "Outgoing Links":
        unique_only = st.checkbox(
            "Export unique links only",
            help="Export only unique outgoing links (removes duplicates)"
        )
    else:
        unique_only = False
    
    if st.button("📤 Export", type="primary"):
        with st.spinner("Preparing export..."):
            data = None
            filename = ""
            
            if export_type == "Outgoing Links":
                if selected_site_id:
                    links = run_async(db.get_outgoing_links_by_site(selected_site_id, unique_only))
                    filename = f"outgoing_links_site_{selected_site_id}"
                else:
                    # Get links for all sites
                    all_links = []
                    for site in sites:
                        links = run_async(db.get_outgoing_links_by_site(site['id'], unique_only))
                        for link in links:
                            link['site_url'] = site['url']
                        all_links.extend(links)
                    links = all_links
                    filename = "outgoing_links_all_sites"
                
                data = links
            
            elif export_type == "Sites Summary":
                data = sites
                filename = "sites_summary"
            
            elif export_type == "Posts List":
                if selected_site_id:
                    posts = run_async(db.get_posts_by_site(selected_site_id))
                    filename = f"posts_site_{selected_site_id}"
                else:
                    all_posts = []
                    for site in sites:
                        posts = run_async(db.get_posts_by_site(site['id']))
                        for post in posts:
                            post['site_url'] = site['url']
                        all_posts.extend(posts)
                    posts = all_posts
                    filename = "posts_all_sites"
                
                data = posts
            
            elif export_type == "Complete Report":
                # Export multiple sheets
                sheets_data = {
                    'Sites': sites,
                    'Crawl History': run_async(db.get_crawl_history(selected_site_id, limit=1000))
                }
                
                if selected_site_id:
                    sheets_data['Posts'] = run_async(db.get_posts_by_site(selected_site_id))
                    sheets_data['Outgoing Links'] = run_async(db.get_outgoing_links_by_site(selected_site_id))
                    filename = f"complete_report_site_{selected_site_id}"
                else:
                    filename = "complete_report_all_sites"
            
            # Export data
            try:
                if export_type == "Complete Report" and export_format == "Excel":
                    filepath = export_multiple_sheets(sheets_data, filename)
                else:
                    if export_format == "CSV":
                        filepath = export_to_csv(data, filename)
                    elif export_format == "Excel":
                        filepath = export_to_excel(data, filename)
                    elif export_format == "JSON":
                        filepath = export_to_json(data, filename)
                
                st.success(f"✅ Export successful!")
                st.info(f"**File saved to:** {filepath}")
                
                # Offer download
                with open(filepath, 'rb') as f:
                    st.download_button(
                        label="⬇️ Download File",
                        data=f,
                        file_name=Path(filepath).name,
                        mime='application/octet-stream'
                    )
                
            except Exception as e:
                st.error(f"❌ Export failed: {str(e)}")


def show_settings():
    """Settings interface"""
    st.title("⚙️ Settings")
    
    # Tabs for different settings
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚫 Excluded Domains",
        "🗺️ Custom Sitemaps",
        "📝 Post Patterns",
        "🔧 Advanced"
    ])
    
    with tab1:
        st.subheader("Excluded Domains")
        st.write("Add domains to exclude from outgoing links extraction (e.g., social media, trackers)")
        
        # Show current excluded domains
        excluded_domains = run_async(db.get_excluded_domains())
        
        st.write(f"**Currently excluded:** {len(excluded_domains)} domains")
        
        if excluded_domains:
            # Display in columns
            cols = st.columns(3)
            for idx, domain in enumerate(excluded_domains):
                with cols[idx % 3]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(domain)
                    with col2:
                        if st.button("🗑️", key=f"del_domain_{idx}"):
                            run_async(db.delete_excluded_domain(domain))
                            st.rerun()
        
        # Add new domain
        st.divider()
        col1, col2 = st.columns([3, 1])
        with col1:
            new_domain = st.text_input(
                "Add New Domain",
                placeholder="example.com",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("➕ Add"):
                if new_domain:
                    run_async(db.add_excluded_domain(new_domain.lower()))
                    st.success(f"Added: {new_domain}")
                    st.rerun()
        
        # Bulk add
        st.divider()
        st.write("**Bulk Add** (one domain per line)")
        bulk_domains = st.text_area("Domains", height=150)
        if st.button("Add All"):
            if bulk_domains:
                domains = [d.strip() for d in bulk_domains.split('\n') if d.strip()]
                for domain in domains:
                    run_async(db.add_excluded_domain(domain.lower()))
                st.success(f"Added {len(domains)} domains")
                st.rerun()
    
    with tab2:
        st.subheader("Custom Sitemap Patterns")
        st.write("Add custom sitemap URL patterns to check")
        st.info("This feature allows you to add site-specific sitemap patterns")
        
        # Implementation similar to excluded domains
        st.text_input("Pattern (e.g., /custom-sitemap.xml)")
        st.button("Add Pattern")
    
    with tab3:
        st.subheader("Post URL Patterns")
        st.write("Add regex patterns to identify post URLs vs pages/categories")
        
        st.text_area(
            "Current Patterns",
            value='\n'.join(POST_URL_PATTERNS),
            height=200,
            disabled=True
        )
        
        st.info("Pattern management coming soon...")
    
    with tab4:
        st.subheader("Advanced Settings")
        
        # Crawler settings
        st.write("**Default Crawler Settings**")
        
        threads = st.slider("Default Threads", 1, 100, DEFAULT_THREADS)
        timeout = st.slider("Request Timeout (seconds)", 5, 120, 30)
        
        if st.button("Save Settings"):
            run_async(db.set_setting('default_threads', str(threads)))
            run_async(db.set_setting('default_timeout', str(timeout)))
            st.success("Settings saved!")
        
        st.divider()
        
        # Database info
        st.write("**Database Information**")
        st.info(f"Database location: {db.db_path}")
        
        # Clear data options
        st.warning("⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data"):
            if st.session_state.get('confirm_clear', False):
                # Clear implementation
                st.error("Clear all data - implementation needed")
                st.session_state.confirm_clear = False
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm")


# if __name__ == "__main__":
#     render_scraper_ui()
