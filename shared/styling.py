"""
Global styling for Analytics Accelerator
Charcoal theme with ultra-thin hover effects
"""

import streamlit as st


def apply_global_styles():
    """Apply global CSS styles to the application"""
    st.markdown(get_unified_css(), unsafe_allow_html=True)


def get_unified_css():
    """Return the unified CSS for all modules - CHARCOAL EDITION"""
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        
        .main {
            background: #f5f5f7;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        @media (prefers-color-scheme: dark) {
            .main { background: #1e1e1e; }
        }
        
        /* ========================================
           CHARCOAL ULTRA-THIN HOVER ON INPUTS
           ======================================== */
        
        /* Hover effect - 0.5px charcoal hairline */
        div.stTextInput:hover > div > div > input {
            border: 0.5px solid #374151 !important;
            transition: border 0.2s ease !important;
        }
        
        div[data-baseweb="input"]:hover {
            border: 0.5px solid #374151 !important;
            border-width: 0.5px !important;
        }
        
        /* Focus effect - matching charcoal */
        div.stTextInput > div > div > input:focus {
            border: 0.5px solid #374151 !important;
        }
        
        div[data-baseweb="input"]:focus {
            border: 0.5px solid #374151 !important;
        }
        
        /* Header */
        .header-ribbon {
            background: linear-gradient(135deg, #e8f4f8 0%, #d4e9f7 100%);
            padding: 24px;
            border-radius: 12px;
            margin: -20px 0 24px 0;
            text-align: center;
        }
        
        @media (prefers-color-scheme: dark) {
            .header-ribbon {
                background: linear-gradient(135deg, #1a3a4a 0%, #0d2a3a 100%);
            }
        }
        
        .header-ribbon h1 {
            color: #6e6e73;
            font-size: 28px;
            font-weight: 400;
            margin: 0;
            letter-spacing: -0.5px;
        }
        
        .header-ribbon p {
            color: #6e6e73;
            margin: 8px 0 0 0;
            font-size: 14px;
        }
        
        @media (prefers-color-scheme: dark) {
            .header-ribbon h1 { color: #a8c5d1; }
            .header-ribbon p { color: #a0a0a0; }
        }
        
        /* Buttons - ALL BLUE */
        .stButton>button {
            background: #0051D5;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 32px;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            background: #003D9E;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,81,213,0.3);
        }
        
        .stDownloadButton>button {
            background: #0051D5;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 32px;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stDownloadButton>button:hover {
            background: #003D9E;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,81,213,0.3);
        }
        
        /* KPI Pills */
        .kpi-container {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        /* Summary badges */
        .summary-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
            margin: 0 8px;
        }
        
        .badge-error {
            background: #ffe5e5;
            color: #d32f2f;
        }
        
        .badge-warning {
            background: #fff4e5;
            color: #f57c00;
        }
        
        .badge-success {
            background: #e8f5e9;
            color: #388e3c;
        }
        
        @media (prefers-color-scheme: dark) {
            .badge-error { background: #3d1a1f; color: #ff8a80; }
            .badge-warning { background: #3d2f1a; color: #ffb74d; }
            .badge-success { background: #1a3d2a; color: #7ddc8f; }
        }
        
        /* Message boxes */
        .success-box {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #34c759;
            margin: 20px 0;
        }
        
        @media (prefers-color-scheme: dark) {
            .success-box {
                background: linear-gradient(135deg, #1a3d2a 0%, #0f2d1f 100%);
                color: #7ddc8f;
            }
        }
        
        .warning-box {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            color: #856404;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #ff9500;
            margin: 20px 0;
        }
        
        @media (prefers-color-scheme: dark) {
            .warning-box {
                background: linear-gradient(135deg, #3d2f1a 0%, #2d1f0f 100%);
                color: #ffb74d;
            }
        }
        
        .error-box {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c2c7 100%);
            color: #721c24;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #ff3b30;
            margin: 20px 0;
        }
        
        @media (prefers-color-scheme: dark) {
            .error-box {
                background: linear-gradient(135deg, #3d1a1a 0%, #2d0f0f 100%);
                color: #ff8a80;
            }
        }
        
        .info-box {
            background: linear-gradient(135deg, #e3f2fd 0%, #d6eaf8 100%);
            color: #1565c0;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #42a5f5;
            margin: 20px 0;
        }
        
        @media (prefers-color-scheme: dark) {
            .info-box {
                background: linear-gradient(135deg, #1a2d3d 0%, #0f1d2d 100%);
                color: #90caf9;
            }
        }
        
        .tip-box {
            background: linear-gradient(135deg, #e3f2fd 0%, #d6eaf8 100%);
            color: #1565c0;
            padding: 15px 20px;
            border-radius: 12px;
            border-left: 4px solid #42a5f5;
            margin: 20px 0;
        }
        
        .tip-box code {
            font-size: 110%;
            font-weight: 500;
        }
        
        @media (prefers-color-scheme: dark) {
            .tip-box {
                background: linear-gradient(135deg, #1a2d3d 0%, #0f1d2d 100%);
                color: #90caf9;
                border-left: 4px solid #42a5f5;
            }
        }
        
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            margin: 10px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        .metric-card h2 {
            text-align: center !important;
            width: 100%;
            display: block;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .metric-card p {
            text-align: center !important;
            width: 100%;
            margin: 5px 0 0 0 !important;
            padding: 0 !important;
        }
        
        @media (prefers-color-scheme: dark) {
            .metric-card {
                background: #2d2d2d;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
            border-bottom: none;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #f5f5f7;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 400;
            color: #6e6e73;
            border: none;
            transition: all 0.2s;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #e8e8ed;
            color: #1d1d1f;
        }
        
        @media (prefers-color-scheme: dark) {
            .stTabs [data-baseweb="tab"] {
                background-color: #2d2d2d;
                color: #86868b;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background-color: #3d3d3d;
                color: #f5f5f7;
            }
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #fafafa !important;
            color: #1d1d1f !important;
            font-weight: 500 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
            border: 1px solid #e5e5ea !important;
        }
        
        @media (prefers-color-scheme: dark) {
            .stTabs [aria-selected="true"] {
                background-color: #1e1e1e !important;
                color: #f5f5f7 !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
                border: 1px solid #424245 !important;
            }
        }
        
        /* File uploader */
        .stFileUploader {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 2px dashed #d1d1d6;
        }
        
        .stFileUploader > div {
            text-align: center;
        }
        
        .stFileUploader label {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        @media (prefers-color-scheme: dark) {
            .stFileUploader {
                background: #2d2d2d;
                border: 2px dashed #48484a;
            }
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
        }
    </style>
    """


def get_header_html(subtitle=""):
    """Return the header HTML"""
    if subtitle:
        return f"""
        <div class="header-ribbon">
            <h1>Analytics Accelerator</h1>
            <p>{subtitle}</p>
        </div>
        """
    else:
        return """
        <div class="header-ribbon" style="padding: 20px;">
            <h1 style="font-size: 28px;">Analytics Accelerator</h1>
        </div>
        """


def get_footer_html():
    """Return empty footer"""
    return ""
