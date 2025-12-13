"""
Help system for Hierarchy Validator
Earth tone colors, geometric icons, expandable sections
"""

import streamlit as st


def show_validation_help():
    """Display comprehensive validation guide with expandable help"""
    
    # Beautiful iOS-style info icon
    info_icon_html = '<svg width="18" height="18" viewBox="0 0 20 20" style="vertical-align: middle; margin-right: 8px;"><circle cx="10" cy="10" r="9" fill="none" stroke="#0051D5" stroke-width="1.5"/><text x="10" y="14" text-anchor="middle" fill="#0051D5" font-size="13" font-weight="600" font-family="system-ui, -apple-system, sans-serif">i</text></svg>'
    
    with st.expander(f"Validation Guide", expanded=False):
        # Add the icon at the top of the content
        st.markdown(f'{info_icon_html}<strong>What This Tool Validates</strong>', unsafe_allow_html=True)
        
        help_html = '''<div style="padding: 10px 10px 10px 26px;">
<ul style="margin-top: 8px;">
<li><strong>Orphaned members:</strong> Parent references that don't exist as members</li>
<li><strong>Parent name mismatches:</strong> Typos, extra spaces, capitalization errors</li>
<li><strong>Duplicate members:</strong> Same name with different parents (causes ambiguity)</li>
<li><strong>Vena restrictions:</strong> Names over 80 characters, invalid characters</li>
<li><strong>Whitespace issues:</strong> Leading/trailing spaces, double spaces, tabs</li>
</ul>
<h4>Issue Severity Levels</h4>
<ul>
<li><svg width="14" height="14" style="vertical-align: middle; margin-right: 6px;"><circle cx="7" cy="7" r="6" fill="#DC2626"/></svg><strong style="color: #DC2626;">Errors:</strong> Will prevent Vena import or cause data corruption</li>
<li><svg width="14" height="14" style="vertical-align: middle; margin-right: 6px;"><circle cx="7" cy="7" r="6" fill="#EA580C"/></svg><strong style="color: #EA580C;">Warnings:</strong> Won't break import but may cause unexpected behavior</li>
<li><svg width="14" height="14" style="vertical-align: middle; margin-right: 6px;"><circle cx="7" cy="7" r="6" fill="#0891B2"/></svg><strong style="color: #0891B2;">Info:</strong> Suggestions for cleaner data quality</li>
</ul>
<h4>Resolution Steps</h4>
<ul>
<li><strong>Orphans:</strong> Add missing parent member or fix typo in parent reference</li>
<li><strong>Mismatches:</strong> Copy correct member name from suggestions</li>
<li><strong>Duplicates:</strong> Rename one instance or merge into single member</li>
<li><strong>Whitespace:</strong> Use download button to get auto-cleaned file</li>
</ul>
<h4>Required File Format</h4>
<ul>
<li><strong>Column: _member_name</strong> - The member (child) name</li>
<li><strong>Column: _parent_name</strong> - The parent name it rolls up to</li>
<li><strong>Optional: _member_alias</strong> - Display name for reporting</li>
<li><strong>Format:</strong> CSV or Excel (.xlsx, .xls)</li>
</ul>
<h4>Best Practices</h4>
<ul>
<li>Run validation before importing to Vena</li>
<li>Fix errors first, then address warnings</li>
<li>Use whitespace download feature for quick cleanup</li>
<li>Keep member names consistent (watch capitalization)</li>
<li>Test with small sample first</li>
</ul>
</div>'''
        st.markdown(help_html, unsafe_allow_html=True)


def get_severity_icon(severity):
    """Return colored circle icon for severity level"""
    colors = {
        'error': '#DC2626',
        'warning': '#EA580C',
        'info': '#0891B2'
    }
    color = colors.get(severity, '#374151')
    return f'<svg width="14" height="14" style="vertical-align: middle; margin-right: 6px;"><circle cx="7" cy="7" r="6" fill="{color}"/></svg>'
