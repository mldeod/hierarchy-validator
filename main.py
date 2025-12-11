#!/usr/bin/env python3
"""
Analytics Accelerator - Excel Analytics Tool
Professional tools for FP&A teams
"""

import streamlit as st
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.modules_config import get_enabled_modules, get_module_tabs, AVAILABLE_MODULES
from shared.styling import get_unified_css, get_header_html, get_footer_html
from shared.workflow import init_workflow_state, receive_workflow_data

# Page config
st.set_page_config(
    page_title="Analytics Accelerator",
    page_icon="assets/logo.svg",  # Your custom logo!
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize workflow state
init_workflow_state()

# Apply unified styling
st.markdown(get_unified_css(), unsafe_allow_html=True)

# Header
st.markdown(get_header_html(), unsafe_allow_html=True)

# Get enabled modules
enabled_modules = get_enabled_modules()
module_tabs_data = get_module_tabs()

if not enabled_modules:
    st.error("No modules are currently enabled. Please contact support.")
    st.stop()

# Create dynamic tabs
tab_names = [name for name, key in module_tabs_data]
tabs = st.tabs(tab_names)

# Render each enabled module in its tab
for idx, (tab_name, module_key) in enumerate(module_tabs_data):
    with tabs[idx]:
        
        # Check if this module should receive workflow data
        has_data, data, source = receive_workflow_data(module_key)
        
        if has_data:
            st.markdown(f"""
            <div class="success-box">
                <h3>✓ Data Received from {AVAILABLE_MODULES[source]['name']}</h3>
                <p>Your data has been automatically loaded and is ready to process.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Render module UI
        if module_key == 'tree_converter':
            from modules.tree_converter import ui as tree_ui
            tree_ui.render()
            
        elif module_key == 'hierarchy_validator':
            from modules.hierarchy_validator import ui as validator_ui
            validator_ui.render(workflow_data=data if has_data else None)
            
        elif module_key == 'data_quality_checker':
            from modules.data_quality_checker import ui as checker_ui
            checker_ui.render()
            
        elif module_key == 'allocation_engine':
            from modules.allocation_engine import ui as allocation_ui
            allocation_ui.render()
        
        else:
            st.warning(f"Module '{module_key}' is enabled but not yet implemented.")

# Footer
st.markdown(get_footer_html(), unsafe_allow_html=True)

# Sidebar - Module info (collapsed by default)
with st.sidebar:
    st.markdown("### Enabled Modules")
    for module_key in enabled_modules:
        module = AVAILABLE_MODULES[module_key]
        st.markdown(f"""
        **{module['icon']} {module['name']}**  
        {module['description']}  
        *Version {module['version']}*
        """)
    
    st.markdown("---")
    st.markdown("### Support")
    st.markdown("Need help? Contact: manu@venaaccelerator.com")
