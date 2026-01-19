"""
Main Entry Point for the Advanced Web Crawler Tool Hub
"""
import streamlit as st
import sys
from pathlib import Path

# Add current directory to path to support imports if needed explicitly
sys.path.append(str(Path(__file__).parent))

# Import configuration and styles
from common.config import PAGE_TITLE, PAGE_ICON, LAYOUT
from common.styles import apply_dark_theme
from common.utils import setup_logging

# Initialize logging
setup_logging()

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Import Tools (Must be after set_page_config because it contains Streamlit commands at module level)
from scraper.ui import render_scraper_ui

# Apply Dark Theme
apply_dark_theme(st)

def main():
    """Main Tool Hub Interface"""
    
    st.sidebar.title("🛠️ Tool Hub")
    
    # Navigation
    tool_options = {
        "🏠 Home": "home",
        "🕷️ Web Scraper": "scraper",
    }
    
    # Session state for navigation
    if "selected_tool" not in st.session_state:
        st.session_state.selected_tool = "home"
        
    selected_label = st.sidebar.radio(
        "Select Tool", 
        list(tool_options.keys()),
        index=0 if st.session_state.selected_tool == "home" else 1
    )
    
    selected_tool = tool_options[selected_label]
    st.session_state.selected_tool = selected_tool
    
    if selected_tool == "home":
        render_home()
    elif selected_tool == "scraper":
        # Render the scraper tool
        render_scraper_ui()

def render_home():
    st.title("🚀 Web Tools Hub")
    
    st.markdown("""
    Welcome to the Web Tools Hub. Select a tool from the sidebar to get started.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
            <div style="font-size: 40px; margin-bottom: 10px;">🕷️</div>
            <h3 style="margin: 0; color: #F8FAFC;">Web Scraper</h3>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 10px;">Crawl sitemaps, extract links, and analyze SEO metadata.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Scraper", use_container_width=True):
             st.session_state.selected_tool = "scraper"
             st.rerun()

    with col2:
        st.markdown("""
        <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; opacity: 0.5;">
            <div style="font-size: 40px; margin-bottom: 10px;">📊</div>
            <h3 style="margin: 0; color: #F8FAFC;">Analytics</h3>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 10px;">Coming Soon: Traffic verification and keyword analysis.</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", disabled=True, use_container_width=True, key="btn_analytics")

    with col3:
        st.markdown("""
        <div style="background-color: #1E293B; padding: 20px; border-radius: 10px; border: 1px solid #334155; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; opacity: 0.5;">
            <div style="font-size: 40px; margin-bottom: 10px;">⚙️</div>
            <h3 style="margin: 0; color: #F8FAFC;">API Tools</h3>
            <p style="color: #94A3B8; font-size: 14px; margin-top: 10px;">Coming Soon: Integration with external APIs.</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", disabled=True, use_container_width=True, key="btn_api")

if __name__ == "__main__":
    main()
