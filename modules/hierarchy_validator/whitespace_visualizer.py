"""
Whitespace Visualizer Module
Handles visualization and cleaning of whitespace issues in hierarchy data
"""

import streamlit as st
import pandas as pd
from io import BytesIO


def visualize_whitespace(text, dark_mode=False):
    """
    Convert text to HTML with highlighted PROBLEM spaces only
    
    Args:
        text: String to visualize
        dark_mode: Boolean for dark mode colors
        
    Returns:
        HTML string with problem spaces highlighted in red backgrounds with dots
    """
    if dark_mode:
        space_bg = "#FF6B6B"
        space_border = "#FF4444"
        text_color = "#E0E0E0"
    else:
        space_bg = "#FFE5E5"
        space_border = "#FF9999"
        text_color = "#333333"
    
    result = ""
    for i, char in enumerate(text):
        if char == ' ':
            # Check if this space is a PROBLEM space
            is_problem = False
            
            # Leading space (position 0)
            if i == 0:
                is_problem = True
            # Trailing space (last position)
            elif i == len(text) - 1:
                is_problem = True
            # First space of a multi-space sequence
            elif i < len(text) - 1 and text[i + 1] == ' ':
                is_problem = True
            # Skip second/third/etc spaces in sequence (already highlighted the first)
            elif i > 0 and text[i - 1] == ' ':
                is_problem = False  # Don't highlight - previous space already highlighted
            
            if is_problem:
                result += f'<span style="background-color: {space_bg}; border: 1px solid {space_border}; padding: 0 2px;">·</span>'
            else:
                # Normal space - just show the dot without highlighting
                result += '·'
        elif char == '\t':
            # Tab character - always a problem!
            result += f'<span style="background-color: {space_bg}; border: 1px solid {space_border}; padding: 0 2px;">⇥</span>'
        else:
            result += char
    
    return f'<span style="font-family: monospace; font-size: 14px; color: {text_color};">{result}</span>'


def clean_whitespace(df, member_col='_member_name', parent_col='_parent_name'):
    """
    Clean all whitespace issues in DataFrame
    
    Args:
        df: DataFrame to clean
        member_col: Name of member column
        parent_col: Name of parent column
        
    Returns:
        Cleaned DataFrame with whitespace removed
    """
    cleaned_df = df.copy()
    
    # Clean member names - remove leading/trailing/double spaces
    if member_col in cleaned_df.columns:
        cleaned_df[member_col] = cleaned_df[member_col].apply(lambda x: ' '.join(str(x).split()) if pd.notna(x) else x)
    
    # Clean parent names
    if parent_col in cleaned_df.columns:
        cleaned_df[parent_col] = cleaned_df[parent_col].apply(lambda x: ' '.join(str(x).split()) if pd.notna(x) else x)
    
    return cleaned_df


def create_whitespace_section(whitespace_issues, df, dark_mode=False):
    """
    Render the complete whitespace issues section with visualizations and downloads
    
    Args:
        whitespace_issues: List of whitespace issue dictionaries
        df: Original DataFrame for generating cleaned version
        dark_mode: Boolean for color scheme
    """
    
    if not whitespace_issues or len(whitespace_issues) == 0:
        return
    
    # Color scheme
    if dark_mode:
        text_color = "#E0E0E0"
        card_bg = "#2D2D2D"
        space_border = "#FF9999"
        warning_color = "#FFA726"
        success_color = "#66BB6A"
    else:
        text_color = "#333333"
        card_bg = "#F9F9F9"
        space_border = "#FF9999"
        warning_color = "#F57C00"
        success_color = "#388E3C"
    
    whitespace_count = len(whitespace_issues)
    
    # Create expander
    with st.expander(f"Whitespace Issues ({whitespace_count} found)", expanded=False):
        
        # Warning box with SVG triangle
        warning_svg = f'''<svg width="20" height="20" viewBox="0 0 20 20" style="vertical-align: middle; margin-right: 8px;">
            <path d="M10 2L2 18h16L10 2z" fill="{warning_color}" stroke="{warning_color}" stroke-width="1.5"/>
            <text x="10" y="14" text-anchor="middle" fill="white" font-size="10" font-weight="bold">!</text>
        </svg>'''
        
        warning_html = f'''
        <div style="padding: 12px; background: #FFF4E5; border-left: 4px solid {warning_color}; border-radius: 4px; margin-bottom: 20px;">
            {warning_svg}
            <strong style="color: {text_color};">Whitespace detected:</strong> 
            {whitespace_count} members contain leading, trailing, or double spaces. 
            Download a cleaned file with all issues automatically fixed.
        </div>
        '''
        st.markdown(warning_html, unsafe_allow_html=True)
        
        st.markdown("### Members with Whitespace Issues")
        
        # Show all visualizations with row numbers
        for idx, issue in enumerate(whitespace_issues):
            issue_html = f'''
            <div style="padding: 14px; margin: 10px 0; background: {card_bg}; border-radius: 6px; border-left: 3px solid {space_border};">
                <div style="margin-bottom: 8px;">
                    <strong style="color: {text_color};">Issue {idx + 1}: Rows {issue['rows']}</strong>
                </div>
                <div style="margin-bottom: 6px; font-size: 13px; color: {text_color}; opacity: 0.8;">
                    Column: <strong>{issue.get('parent_name', 'N/A')}</strong>
                </div>
                <div style="margin-bottom: 6px; font-size: 12px; color: {warning_color};">
                    {issue['issue_type']} ({issue['space_count']} space(s))
                </div>
                <div style="padding: 8px; background: rgba(255,255,255,0.5); border-radius: 4px;">
                    {visualize_whitespace(issue['member_name'], dark_mode)}
                </div>
            </div>
            '''
            st.markdown(issue_html, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Download section
        st.markdown("### Download Cleaned File")
        
        # Generate cleaned DataFrame
        cleaned_df = clean_whitespace(df)
        
        # CSV
        csv_buffer = BytesIO()
        cleaned_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            cleaned_df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        excel_data = excel_buffer.getvalue()
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="hierarchy_cleaned.csv",
                mime="text/csv",
                width='stretch'
            )
        
        with col2:
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="hierarchy_cleaned.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
        
        with col3:
            checkmark_svg = f'''<svg width="16" height="16" viewBox="0 0 16 16" style="vertical-align: middle; margin-right: 6px;">
                <circle cx="8" cy="8" r="7" fill="{success_color}"/>
                <path d="M5 8l2 2 4-4" stroke="white" stroke-width="2" fill="none" stroke-linecap="round"/>
            </svg>'''
            
            success_html = f'''
            <div style="padding: 12px; background: #E8F5E9; border-radius: 6px; font-size: 13px; display: flex; align-items: center;">
                {checkmark_svg}
                <span style="color: {text_color};">{whitespace_count} issues will be fixed</span>
            </div>
            '''
            st.markdown(success_html, unsafe_allow_html=True)
