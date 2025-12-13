"""
Shared Tooltip Component
Reusable tooltip helper for all Analytics Accelerator modules
"""

def get_info_circle_icon(color="#0051D5"):
    """Generate clean geometric info icon (circle with lowercase i)"""
    return f'''<svg width="18" height="18" viewBox="0 0 18 18" style="vertical-align: middle; margin-right: 8px;">
        <circle cx="9" cy="9" r="8" fill="none" stroke="{color}" stroke-width="1.5"/>
        <text x="9" y="13" text-anchor="middle" fill="{color}" font-size="12" font-weight="600" font-family="system-ui, -apple-system, sans-serif">i</text>
    </svg>'''

def get_error_icon(color="#DC2626"):
    """Generate clean geometric error icon (filled circle)"""
    return f'''<svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align: middle; margin-right: 6px;">
        <circle cx="7" cy="7" r="6" fill="{color}"/>
    </svg>'''

def get_warning_icon(color="#F59E0B"):
    """Generate clean geometric warning icon (filled circle)"""
    return f'''<svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align: middle; margin-right: 6px;">
        <circle cx="7" cy="7" r="6" fill="{color}"/>
    </svg>'''

def get_info_icon(color="#3B82F6"):
    """Generate clean geometric info icon (filled circle)"""
    return f'''<svg width="14" height="14" viewBox="0 0 14 14" style="vertical-align: middle; margin-right: 6px;">
        <circle cx="7" cy="7" r="6" fill="{color}"/>
    </svg>'''

def create_tooltip(text, tooltip_text):
    """
    Create an inline tooltip with hover functionality
    
    Args:
        text: The label text to display
        tooltip_text: The help text shown on hover
        
    Returns:
        HTML string with tooltip
    
    Example:
        st.markdown(create_tooltip("Dimension Name", "Enter your Vena dimension (e.g., Account, Cost Center)"), unsafe_allow_html=True)
    """
    tooltip_html = f'''
    <div style="display: inline-block;">
        {text}
        <span class="tooltip-icon" style="
            display: inline-block;
            margin-left: 6px;
            width: 16px;
            height: 16px;
            background: #0051D5;
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 16px;
            font-size: 11px;
            font-weight: bold;
            cursor: help;
            position: relative;
        " title="{tooltip_text}">?</span>
    </div>
    '''
    return tooltip_html


def create_help_section(title, content, expanded=False):
    """
    Create an expandable help section
    
    Args:
        title: Section title (e.g., "Need Help?")
        content: HTML content for the help section
        expanded: Whether section starts expanded (default: False)
        
    Returns:
        Streamlit expander with help content
    
    Example:
        with create_help_section("Need Help?", help_html):
            # Content renders inside
    """
    import streamlit as st
    return st.expander(title, expanded=expanded)


# Pre-built tooltip texts for common fields
TOOLTIPS = {
    # Tree Converter
    'dimension_name': 'Enter your Vena dimension name (e.g., Account, Cost Center, Products)',
    'tree_upload': 'Excel file with hierarchy in columns A-J, aliases in K, operators in L',
    'operator': '+ (add), - (subtract), ~ (ignore) - defaults to + if blank',
    
    # Hierarchy Validator
    'validator_upload': 'CSV or Excel file with _member_name and _parent_name columns',
    'member_name': 'The child member name in the hierarchy',
    'parent_name': 'The parent this member rolls up to',
    'member_alias': 'Optional display name for reporting (not used in calculations)',
    
    # Issue Types
    'orphan': 'Parent reference exists but no matching member found - will cause Vena import errors',
    'mismatch': 'Parent name has typo or extra spaces - Vena won\'t match it correctly',
    'duplicate': 'Same member name appears multiple times with different parents - creates ambiguity',
    'whitespace': 'Leading/trailing spaces or double spaces - can cause matching issues',
    'vena_restriction': 'Violates Vena naming rules (80 char limit, invalid characters)',
}
