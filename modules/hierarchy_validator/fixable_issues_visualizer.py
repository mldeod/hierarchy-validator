"""
Fixable Issues Visualizer V2 - Diagnostic Command Center
Phase 2 Iteration 3 - Auditor-Approved Hybrid Design

Design Philosophy:
- Progressive Disclosure: Pills → Table → Detail
- Lightbox Effect: Dark UI → White Inspection Zones  
- Diagnostic Command Center: Empowering users to fix systematically

Approved by: The Auditor (December 30, 2025)
Built by: Manu + Claude
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from io import BytesIO
from shared.styling import DesignTokens  # For detail border token governance


# ============================================================================
# UTILITY FUNCTIONS (Preserved from V1 - These are brilliant!)
# ============================================================================

def has_whitespace_issues(text):
    """Check if text has any whitespace problems"""
    if not text:
        return False
    return (text[0] == ' ' or text[-1] == ' ' or '\t' in text or '  ' in text)


def has_character_typo(member_name, parent_ref):
    """
    Check if difference is a CHARACTER typo (not just whitespace)
    Returns True only if there are non-whitespace character differences
    """
    from rapidfuzz import distance
    
    # Clean both - remove all whitespace for comparison
    member_clean = member_name.strip().replace('\t', ' ').replace('  ', ' ')
    parent_clean = parent_ref.strip().replace('\t', ' ').replace('  ', ' ')
    
    # If they match after cleaning, it's ONLY a whitespace issue
    if member_clean == parent_clean:
        return False
    
    # There's a real character difference
    return True


def highlight_whitespace_issues(text):
    """
    Highlight ONLY problem whitespace (leading/trailing/tabs/double)
    Returns: html_with_highlights showing the problem
    
    PRESERVED FROM V1 - This logic is brilliant!
    """
    result = []
    
    # Check for leading spaces
    leading_count = 0
    if text and text[0] == ' ':
        leading_count = len(text) - len(text.lstrip(' '))
        for i in range(leading_count):
            result.append('<span style="background-color: #ffebee; padding: 2px 4px; margin: 0 1px; border-radius: 2px;">·</span>')
        text = text[leading_count:]
    
    # Check for trailing spaces (process from end)
    trailing_count = 0
    if text and text[-1] == ' ':
        trailing_count = len(text) - len(text.rstrip(' '))
        text = text[:-trailing_count]
    
    # Process middle (tabs and double spaces)
    i = 0
    while i < len(text):
        char = text[i]
        
        # Tab
        if char == '\t':
            result.append('<span style="background-color: #ffebee; padding: 2px 6px; margin: 0 1px; border-radius: 2px;">→</span>')
            i += 1
        # Double space
        elif char == ' ' and i + 1 < len(text) and text[i + 1] == ' ':
            # Count consecutive spaces
            space_count = 0
            j = i
            while j < len(text) and text[j] == ' ':
                space_count += 1
                j += 1
            
            # Highlight all consecutive spaces
            for _ in range(space_count):
                result.append('<span style="background-color: #ffebee; padding: 2px 4px; margin: 0 1px; border-radius: 2px;">·</span>')
            i = j
        else:
            result.append(char)
            i += 1
    
    # Add trailing spaces
    for i in range(trailing_count):
        result.append('<span style="background-color: #ffebee; padding: 2px 4px; margin: 0 1px; border-radius: 2px;">·</span>')
    
    return ''.join(result)

# ============================================================================

# ============================================================================
# TEXT DIFF ENGINE - Beautiful Mille-Feuille Architecture (V3.0.0)
# ============================================================================
# Import the industrial-grade modular diff engine
from .text_diff_engine import highlight_differences

def categorize_issues(issues_list):
    """
    Count individual variations (sub-issues), not groups.
    
    NEW LOGIC: We resolve issues individually (each variation is separate).
    We present them grouped by member name (for readability).
    
    Categories:
    - whitespace: Count of whitespace variations
    - typo: Count of typo variations (parent mismatches)
    
    NO "both" category - we count each variation type separately.
    """
    whitespace_variations = []
    typo_variations = []
    
    for issue in issues_list:
        for variation in issue['variations']:
            # Each variation is counted individually
            if variation.get('has_typo', False):
                typo_variations.append({
                    'issue': issue,
                    'variation': variation
                })
            else:
                whitespace_variations.append({
                    'issue': issue,
                    'variation': variation
                })
    
    return {
        'whitespace': whitespace_variations,
        'typo': typo_variations
    }


def prepare_table_data(issues_list, categorized):
    """
    Convert issues into flat table rows for GDG display
    
    Columns (Auditor-approved):
    - Type: Whitespace / Typo / Both
    - Problem: Full text (WRAPPED, not truncated!)
    - Fix: Full text (WRAPPED)
    - Rows: Smart formatting
    
    Auditor's Decision: Removed "Variations" column - it's technical detail
    that belongs in the Detail Box, not the scannable overview table.
    """
    table_rows = []
    
    for issue in issues_list:
        # Determine type by checking variations
        has_whitespace_var = any(not v.get('has_typo', False) for v in issue['variations'])
        has_typo_var = any(v.get('has_typo', False) for v in issue['variations'])
        
        if has_whitespace_var and has_typo_var:
            issue_type = 'Mixed'  # This member has both types of sub-issues
        elif has_typo_var:
            issue_type = 'Typo'
        else:
            issue_type = 'Whitespace'
        
        # Get first variation's problem text (NO TRUNCATION - Auditor approved wrapping!)
        problem_text = issue['variations'][0]['problem_text']
        
        # Get correct text (NO TRUNCATION)
        correct_text = issue['correct_text']
        
        # Format rows (smart truncation for display)
        all_rows = issue['all_rows']
        if len(all_rows) <= 5:
            rows_str = ', '.join(map(str, [r+2 for r in all_rows]))
        else:
            first_five = ', '.join(map(str, [r+2 for r in all_rows[:5]]))
            rows_str = f"{first_five}... +{len(all_rows)-5}"
        
        table_rows.append({
            'Type': issue_type,
            'Problem': problem_text,
            'Fix': correct_text,
            'Rows': rows_str,
            '_issue_idx': len(table_rows),  # Hidden index for selection
            '_first_row': all_rows[0] if all_rows else 999999  # For sorting
        })
    
    df = pd.DataFrame(table_rows)
    
    # Sort by Type (Whitespace → Typo → Both), then by first row
    # Auditor's Decision: "Mental mode batching"
    type_order = {'Whitespace': 1, 'Typo': 2, 'Both': 3}
    df['_type_order'] = df['Type'].map(type_order)
    df = df.sort_values(['_type_order', '_first_row'])
    df = df.drop(columns=['_type_order', '_first_row'])
    
    return df


def render_category_pills(categorized):
    """
    Render two category pills showing variation counts
    
    NEW: Count individual variations (sub-issues), not groups.
    Only 2 categories: Whitespace | Typos
    """
    whitespace_count = len(categorized['whitespace'])
    typo_count = len(categorized['typo'])
    
    pills_html = f'''
    <div style="display: flex; justify-content: space-evenly; margin: 20px 0;">
        <span class="fixable-pill fixable-pill-whitespace">{whitespace_count} Whitespace Issues</span>
        <span class="fixable-pill fixable-pill-typo">{typo_count} Typo Issues</span>
    </div>
    '''
    st.markdown(pills_html, unsafe_allow_html=True)


def render_detail_box(issue, categorized):
    """
    Render the detailed highlighting for a selected issue
    
    REUSES existing highlighting logic - the magic is preserved!
    
    Auditor's Insight: "The variation count belongs HERE, not in the table.
    It keeps the GDG table as a 'clean grid' and makes the Detail Box feel more valuable."
    """
    correct_text = issue['correct_text']
    variations = issue['variations']
    variation_count = len(variations)
    
    # Determine border color by checking what types of variations this issue has
    has_whitespace_var = any(not v.get('has_typo', False) for v in variations)
    has_typo_var = any(v.get('has_typo', False) for v in variations)
    
    if has_whitespace_var and has_typo_var:
        border_color = DesignTokens.FIXABLE['detail_border_both']  # Mixed
    elif has_typo_var:
        border_color = DesignTokens.FIXABLE['detail_border_typo']
    else:
        border_color = DesignTokens.FIXABLE['detail_border_whitespace']
    
    # Build variation display
    if variation_count == 1:
        # Single variation - show it normally
        var = variations[0]
        visual = highlight_differences(correct_text, var['problem_text'])
        var_rows = ', '.join(map(str, [r + 2 for r in var['rows']]))
        
        st.markdown(f"""
        <div style="
            margin: 15px 0; 
            padding: 15px; 
            background: #ffffff; 
            border-left: 3px solid {border_color};
            border-radius: 12px;
        ">
            <div style="font-family: monospace; font-size: 14px; margin-bottom: 8px;">
                {visual}
            </div>
            <div style="font-size: 11px; color: #999; margin-bottom: 8px;">
                Rows: {var_rows}
            </div>
            <div style="font-size: 12px; color: #999; margin-bottom: 8px;">↓</div>
            <div style="font-family: monospace; font-size: 14px; color: #16a34a; font-weight: 500;">
                {correct_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Multiple variations - show all of them
        st.markdown(f"""
        <div style="
            margin: 15px 0; 
            padding: 15px; 
            background: #ffffff; 
            border-left: 3px solid {border_color};
            border-radius: 12px;
        ">
            <div style="font-size: 12px; color: #666; margin-bottom: 10px; font-weight: 500;">
                {variation_count} variations → same fix:
            </div>
        """, unsafe_allow_html=True)
        
        # Render each variation
        for var in variations:
            var_rows = ', '.join(map(str, [r + 2 for r in var['rows']]))
            visual = highlight_differences(correct_text, var['problem_text'])
            
            st.markdown(f"""
            <div style="margin-bottom: 10px; padding: 8px; background: #fafafa; border-radius: 4px;">
                <div style="font-family: monospace; font-size: 13px; margin-bottom: 4px;">
                    {visual}
                </div>
                <div style="font-size: 11px; color: #999;">
                    Rows: {var_rows}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Show the fix result
        st.markdown(f"""
            <div style="font-size: 12px; color: #999; margin: 12px 0 8px 0;">↓</div>
            <div style="font-family: monospace; font-size: 14px; color: #16a34a; font-weight: 500;">
                {correct_text}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PRESERVED GROUPING LOGIC (V1) - This is brilliant, don't touch it!
# ============================================================================

def get_grouping_key(text):
    """
    Normalize text for grouping - strips and collapses whitespace
    This ensures variations group together correctly
    """
    return ' '.join(text.split())


def render_fixable_section(fixable_issues, df):
    """
    Display fixable issues section - GROUPED BY MEMBER ARCHITECTURE (V2.6)
    
    MAJOR CHANGE: Groups issues by member name for cleaner UX
    - Table: One row per member (showing all issue IDs)
    - Detail: Big HTML blob with all issues for selected member
    
    POC for future complex diagnostics (AI variance analysis, allocation validation, etc.)
    Foundation built right, scales to anything.
    
    Args:
        fixable_issues: List of issue dicts from final_table with Category in ['Whitespace', 'Parent Mismatch']
        df: Original dataframe (for generating download)
    """
    
    if not fixable_issues:
        st.markdown("---")
        st.markdown("### Fixable Issues")
        st.markdown('<div class="fixable-pill fixable-pill-success">✓ 0 Fixable Issues - Data is Clean!</div>',
                   unsafe_allow_html=True)
        return
    
    # ========================================================================
    # STEP 1: COUNT BY CATEGORY (for pills)
    # ========================================================================
    whitespace_count = sum(1 for issue in fixable_issues if issue['Category'] == 'Whitespace')
    typo_count = sum(1 for issue in fixable_issues if issue['Category'] == 'Parent Mismatch')
    
    # ========================================================================
    # STEP 2: RENDER SECTION HEADER & PILLS
    # ========================================================================
    st.markdown("---")
    st.markdown("### Fixable Issues")
    
    pills_html = f'''
    <div style="display: flex; justify-content: space-evenly; margin: 20px 0;">
        <span class="fixable-pill fixable-pill-whitespace">{whitespace_count} Whitespace Issues</span>
        <span class="fixable-pill fixable-pill-typo">{typo_count} Parent Mismatch</span>
    </div>
    '''
    st.markdown(pills_html, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================================================
    # STEP 3: GROUP ISSUES BY MEMBER NAME
    # ========================================================================
    # Note: Family grouping already done in ui.py when errorlist.csv was created.
    # Family numbers in Issue field (e.g., #5.1, #5.2, #5.3) indicate the family.
    # We just need to group for DISPLAY purposes (one row per member in table).
    #
    # Import clean_name from the new module (DRY - don't duplicate!)
    # ========================================================================
    from collections import defaultdict
    from .issue_family_grouping import clean_name
    
    member_groups = defaultdict(list)
    
    for issue in fixable_issues:
        # ALWAYS use cleaned member name for grouping (consistent with ui.py)
        # This fixes the bug where Parent Mismatch issues weren't being cleaned
        if issue['Member Name'] != '—':
            # Use cleaned member name
            member_name = clean_name(issue['Member Name']) or issue['Member Name']
        else:
            # Orphan - use parent name with indicator
            member_name = f"(Orphan) {issue['Parent Name']}"
        
        member_groups[member_name].append(issue)
    
    # ========================================================================
    # STEP 4: BUILD GROUPED TABLE DATA
    # ========================================================================
    table_data = []
    
    for member_name, issues in member_groups.items():
        # Collect issue IDs
        issue_ids = ', '.join([issue['Issue'] for issue in issues])
        
        # Count total rows affected (parse Rows field)
        total_rows = 0
        for issue in issues:
            rows_str = str(issue['Rows'])
            # Count commas + 1 for simple count (not perfect but good enough)
            if ',' in rows_str:
                total_rows += rows_str.count(',') + 1
            else:
                total_rows += 1
        
        table_data.append({
            'Member Name': member_name,
            'Issues': issue_ids,
            'Rows': total_rows,
            '_issues_list': issues  # Hidden: full issue objects for detail view
        })
    
    # Sort by member name for consistency
    table_data = sorted(table_data, key=lambda x: x['Member Name'])
    
    # ========================================================================
    # STEP 5: DISPLAY GROUPED TABLE
    # ========================================================================
    if 'fixable_expander_open' not in st.session_state:
        st.session_state.fixable_expander_open = False
    
    with st.expander("View Fixable Issues Details", expanded=st.session_state.fixable_expander_open):
        if not st.session_state.fixable_expander_open:
            st.session_state.fixable_expander_open = True
        
        st.markdown("#### Issues Overview")
        
        # Create display dataframe (without hidden _issues_list column)
        display_df = pd.DataFrame([
            {
                'Member Name': row['Member Name'],
                'Issues': row['Issues'],
                'Rows': row['Rows']
            }
            for row in table_data
        ])
        
        # Display with selection
        event = st.dataframe(
            display_df,
            hide_index=True,
            width='stretch',
            on_select='rerun',
            selection_mode='single-row',
            key='fixable_issues_grouped_table',
            column_config={
                'Member Name': st.column_config.TextColumn('Member Name', width=400),
                'Issues': st.column_config.TextColumn('Issues', width=300),
                'Rows': st.column_config.NumberColumn('Rows', width=100)
            }
        )
        
        # ====================================================================
        # STEP 6: HANDLE SELECTION - RENDER BIG HTML BLOB FOR ALL ISSUES
        # ====================================================================
        if event and hasattr(event, 'selection') and event.selection.get('rows'):
            selected_rows = event.selection['rows']
            if selected_rows:
                st.session_state.fixable_expander_open = True
                selected_idx = selected_rows[0]
                selected_member_data = table_data[selected_idx]
                selected_member_name = selected_member_data['Member Name']
                selected_issues = selected_member_data['_issues_list']
                
                # Render detail section with ALL issues for this member
                st.markdown("#### Issue Details")
                st.markdown(f"**{selected_member_name}** ({len(selected_issues)} issue{'s' if len(selected_issues) > 1 else ''})")
                
                # Build one big HTML blob with all issue detail boxes stacked
                render_member_issues_blob(selected_issues)
    
    # ========================================================================
    # STEP 7: DOWNLOAD BUTTON
    # ========================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Apply fixes to dataframe
    fixed_df = df.copy()
    
    for issue in fixable_issues:
        if issue['Category'] == 'Parent Mismatch':
            problem = issue['Parent Name']
            fix = issue['Member Name']
        else:
            if issue['Member Name'] != '—':
                problem = issue['Member Name']
                fix = issue['Member Name'].strip().replace('\t', ' ').replace('  ', ' ')
            else:
                problem = issue['Parent Name']
                fix = issue['Parent Name'].strip().replace('\t', ' ').replace('  ', ' ')
        
        # Replace in both columns
        fixed_df['_member_name'] = fixed_df['_member_name'].replace(problem, fix)
        fixed_df['_parent_name'] = fixed_df['_parent_name'].replace(problem, fix)
    
    # Download
    from io import BytesIO
    csv_buffer = BytesIO()
    fixed_df.to_csv(csv_buffer, index=False)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    st.download_button(
        label="Download Fixed File",
        data=csv_buffer.getvalue(),
        file_name=f"hierarchy_fixed_{timestamp}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )


def render_member_issues_blob(issues):
    """
    Render ALL issues for a member in one big HTML blob
    Stacks all detail boxes vertically - scrollable if many
    
    V2.8 - SCANDINAVIAN FINANCE GRADE STYLING
    - Clean chunk highlighting for parent mismatches
    - Background-only rounded pills for whitespace (no characters!)
    - Pill-matching border colors (richer red/orange)
    - Professional divider with "FIXED" label
    - Dark mode ready
    
    This is the foundation for future complex diagnostics:
    - AI variance explanations
    - Multi-step allocation validation
    - Dependency chain visualization
    
    Args:
        issues: List of issue dicts for a single member
    """
    
    # Get design tokens
    tokens = DesignTokens.DETAIL_CARDS
    
    # Build CSS for detail cards (inline for Streamlit compatibility)
    css = f"""
    <style>
        .detail-card {{
            background: {tokens['bg_light']};
            border-radius: {tokens['border_radius']};
            padding: {tokens['card_padding']};
            margin: {tokens['card_margin']};
            border-left: {tokens['border_width']} solid transparent;
            box-shadow: {tokens['shadow_light']};
            transition: all 0.2s ease;
        }}
        
        .detail-card:hover {{
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 2px 4px rgba(0, 0, 0, 0.06);
            transform: translateY(-1px);
        }}
        
        .detail-card.error {{
            border-left-color: {DesignTokens.PILLS['error_bg_light']}; /* Match pill red */
        }}
        
        .detail-card.warning {{
            border-left-color: {DesignTokens.PILLS['warning_bg_light']}; /* Match pill orange */
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: {tokens['element_spacing']};
        }}
        
        .issue-info {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .issue-number {{
            font-size: {tokens['font_size_header']};
            font-weight: {tokens['font_weight_header']};
            color: {tokens['text_header_light']};
        }}
        
        .issue-divider {{
            color: {DesignTokens.LIGHT['border']};
            font-weight: 300;
        }}
        
        .issue-category {{
            font-size: {tokens['font_size_header']};
            font-weight: 500;
            color: {tokens['text_meta_light']};
        }}
        
        .issue-rows {{
            font-size: {tokens['font_size_meta']};
            color: {tokens['text_label_light']};
            font-weight: 400;
            margin-left: 12px;
        }}
        
        .card-problem {{
            font-family: {tokens['font_family_mono']};
            font-size: {tokens['font_size_code']};
            color: {tokens['text_code_light']};
            margin-bottom: {tokens['element_spacing']};
            padding: 8px 0;
            line-height: 1.5;
        }}
        
        .card-problem .highlight-error {{
            background-color: #fee2e2;
            color: #991b1b;
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 500;
        }}
        
        .card-divider {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin: {tokens['element_spacing']} 0;
        }}
        
        .divider-line {{
            flex: 1;
            height: 1px;
            background: #e5e5e7;
        }}
        
        .divider-label {{
            font-size: {tokens['font_size_label']};
            font-weight: 600;
            color: {tokens['text_label_light']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .card-solution {{
            font-family: {tokens['font_family_mono']};
            font-size: {tokens['font_size_code']};
            color: {tokens['text_success_light']};
            font-weight: {tokens['font_weight_fixed']};
            padding: 8px 0;
        }}
        
        /* Dark mode */
        @media (prefers-color-scheme: dark) {{
            .detail-card {{
                background: {tokens['bg_dark']};
                box-shadow: {tokens['shadow_dark']};
            }}
            
            .detail-card.error {{
                border-left-color: {DesignTokens.PILLS['error_bg_dark']};
            }}
            
            .detail-card.warning {{
                border-left-color: {DesignTokens.PILLS['warning_bg_dark']};
            }}
            
            .issue-number {{
                color: {tokens['text_header_dark']};
            }}
            
            .issue-divider {{
                color: {DesignTokens.DARK['border']};
            }}
            
            .issue-category {{
                color: {tokens['text_meta_dark']};
            }}
            
            .issue-rows {{
                color: {tokens['text_label_dark']};
            }}
            
            .card-problem {{
                color: {tokens['text_code_dark']};
            }}
            
            .card-problem .highlight-error {{
                background-color: #7f1d1d;
                color: #fca5a5;
            }}
            
            .divider-line {{
                background: #2a2a2a;
            }}
            
            .divider-label {{
                color: {tokens['text_label_dark']};
            }}
            
            .card-solution {{
                color: {tokens['text_success_dark']};
            }}
        }}
    </style>
    """
    
    # Build complete HTML document for components.html()
    # This is necessary because components.html() renders in an iframe
    html_parts = ['<div style="font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', sans-serif;">']
    html_parts.append(css)
    
    # Now render each card HTML
    for idx, issue in enumerate(issues):
        # Determine card class based on category
        card_class = 'error' if issue['Category'] == 'Parent Mismatch' else 'warning'
        
        # Extract problem and fix text
        if issue['Category'] == 'Parent Mismatch':
            problem = issue['Parent Name']
            fix = issue['Member Name']
        else:
            if issue['Member Name'] != '—':
                problem = issue['Member Name']
                fix = issue['Member Name'].strip().replace('\t', ' ').replace('  ', ' ')
            else:
                problem = issue['Parent Name']
                fix = issue['Parent Name'].strip().replace('\t', ' ').replace('  ', ' ')
        
        # Generate visual comparison with highlighting
        visual_html = highlight_differences(fix, problem)
        
        # Build card HTML using string concatenation to avoid escaping
        card_html = (
            '<div class="detail-card ' + card_class + '">'
            '<div class="card-header">'
            '<div class="issue-info">'
            '<span class="issue-number">' + issue['Issue'] + '</span>'
            '<span class="issue-divider">·</span>'
            '<span class="issue-category">' + issue['Category'] + '</span>'
            '</div>'
            '<span class="issue-rows">Rows: ' + issue['Rows'] + '</span>'
            '</div>'
            '<div class="card-problem">' + visual_html + '</div>'
            '<div class="card-divider">'
            '<div class="divider-line"></div>'
            '<span class="divider-label">Fixed</span>'
            '<div class="divider-line"></div>'
            '</div>'
            '<div class="card-solution">' + fix + '</div>'
            '</div>'
        )
        
        html_parts.append(card_html)
    
    html_parts.append('</div>')
    
    # Combine and render using components.html (which doesn't escape HTML)
    full_html = '\n'.join(html_parts)
    
    # Calculate height based on number of issues (each card ~200px + margins)
    height = min(800, len(issues) * 220 + 50)
    
    components.html(full_html, height=height, scrolling=True)
