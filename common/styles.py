DARK_THEME_CSS = """
<style>
    /* Global Settings */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #F8FAFC !important;
    }
    
    .stApp {
        background-color: #0F172A;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6, .stMarkdown, p, li, label {
        color: #F1F5F9 !important;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    
    h1 { margin-bottom: 2rem; }
    
    /* Metrics / Cards */
    [data-testid="stMetric"] {
        background-color: #1E293B;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #334155;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.15);
        border-color: #3B82F6;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-weight: 700;
        font-size: 1.875rem;
    }

    /* Buttons */
    .stButton > button {
        background-color: #3B82F6;
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    }
    
    .stButton > button:hover {
        background-color: #2563EB;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
    }

    button[kind="secondary"] {
        background-color: #1E293B;
        color: #E2E8F0 !important;
        border: 1px solid #475569;
    }
    
    button[kind="secondary"]:hover {
        background-color: #334155;
        color: #F8FAFC !important;
        border-color: #64748B;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1F2937;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Sidebar Navigation Text */
    section[data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        color: #3B82F6 !important;
    }

    /* Dataframes */
    .stDataFrame {
        border: 1px solid #334155;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3B82F6 0%, #60A5FA 100%);
        border-radius: 9999px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #1E293B;
        border: 1px solid #334155;
        color: #F1F5F9 !important; 
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    .streamlit-expanderHeader p {
        color: #F1F5F9 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 1.5rem;
        color: #E2E8F0;
    }

    /* Custom Boxes */
    .info-box {
        background-color: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: #93C5FD !important;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .success-box {
        background-color: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.2);
        color: #4ADE80 !important;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    .warning-box {
        background-color: rgba(234, 179, 8, 0.1);
        border: 1px solid rgba(234, 179, 8, 0.2);
        color: #FDE047 !important;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }

    /* Inputs */
    .stTextInput input, .stSelectbox, .stNumberInput input, .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        padding: 0.5rem 0.75rem !important;
        background-color: #1E293B !important;
        color: #F8FAFC !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border-color: #334155 !important;
        color: #F8FAFC !important;
    }
    
    div[data-baseweb="select"] span {
        color: #F8FAFC !important;
    }
    
    div[data-baseweb="popover"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
    }
    
    div[data-baseweb="menu"] {
        background-color: #1E293B !important;
    }
    
    div[data-baseweb="menu"] li:hover {
        background-color: #334155 !important;
    }
    
    /* Force check boxes and radios to blue */
    .stCheckbox > label > div[role="checkbox"][aria-checked="true"] {
        background-color: #3B82F6 !important;
        border-color: #3B82F6 !important;
    }
    
    .stRadio > label {
        color: #E2E8F0 !important;
    }

    /* Message colors */
    .stSuccess {
        background-color: rgba(34, 197, 94, 0.1) !important;
        color: #4ADE80 !important;
    }
    .stInfo {
        background-color: rgba(59, 130, 246, 0.1) !important;
        color: #93C5FD !important;
    }


    /* Link Style */
    a {
        color: #60A5FA;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
        color: #93C5FD;
    }

</style>
"""

def apply_dark_theme(st):
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
