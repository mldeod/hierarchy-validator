"""
Hierarchy Validator Module - UI Layer (v8 Elegant)
Validate parent-child hierarchies with comprehensive error detection
Beautiful light-themed presentation
"""

import streamlit as st
import pandas as pd
from collections import defaultdict

# Import validation engine
from modules.hierarchy_validator.validation_engine import (
    find_orphans,
    find_parent_mismatches,
    find_duplicate_members,
    find_whitespace_issues
)

def render(workflow_data=None):
    """
    Render the Hierarchy Validator module with v8 elegant styling
    
    Args:
        workflow_data: DataFrame passed from another module (optional)
    """
    
    # File upload or workflow data
    if workflow_data is not None:
        df = workflow_data
        uploaded_file = None
    else:
        st.markdown("### Validate Parent-Child Hierarchy")
        
        st.markdown("""
        <div class="info-box">
            <p><strong>Comprehensive hierarchy validation including:</strong></p>
            <ul>
                <li>Orphaned members (parent doesn't exist)</li>
                <li>Parent name mismatches (typos, whitespace)</li>
                <li>Duplicate members with different parents</li>
                <li>Vena naming restrictions (80+ chars, special characters)</li>
                <li>Whitespace issues (leading/trailing spaces, tabs)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload parent-child hierarchy file",
            type=['xlsx', 'xls', 'csv'],
            help="Must contain _member_name and _parent_name columns"
        )
        
        if not uploaded_file:
            return
        
        # Read file
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            return
    
    # Validate required columns
    if '_member_name' not in df.columns or '_parent_name' not in df.columns:
        st.error("❌ Missing required columns: `_member_name` and `_parent_name`")
        return
    
    # Run validation
    with st.spinner('Running validation checks...'):
        orphans = find_orphans(df, max_edit_distance=2)
        mismatches = find_parent_mismatches(df, max_edit_distance=2)
        duplicate_errors, duplicate_warnings = find_duplicate_members(df)
        whitespace_issues = find_whitespace_issues(df)
    
    total_errors = len(orphans) + len(mismatches) + len(duplicate_errors)
    total_warnings = len(duplicate_warnings) + len(whitespace_issues)
    
    # Summary badges
    if total_errors == 0 and total_warnings == 0:
        st.markdown('<div style="text-align: center; margin: 20px 0;"><span class="summary-badge badge-success">✓ No issues found</span></div>', unsafe_allow_html=True)
    else:
        summary_html = '<div style="text-align: center; margin: 20px 0;">'
        if total_errors > 0:
            summary_html += f'<span class="summary-badge badge-error">{total_errors} error{"s" if total_errors > 1 else ""}</span>'
        if total_warnings > 0:
            summary_html += f'<span class="summary-badge badge-warning">{total_warnings} warning{"s" if total_warnings > 1 else ""}</span>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)
        
        # Build master table
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        
        master_table = []
        issue_num = 1
        
        # ORPHANS - Most critical! Parent doesn't exist at all
        for parent_str, data in orphans.items():
            excel_rows = [r + 2 for r in data['rows']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            # Build cause explanation
            cause = "parent doesn't exist as member"
            if data['has_whitespace']:
                if data['is_vena_invalid']:
                    cause += " (also has vena-invalid whitespace)"
                else:
                    cause += " (also has whitespace issues)"
            
            # Fix Vena capitalization then capitalize first letter
            cause = cause.replace("vena", "Vena")
            cause = cause[0].upper() + cause[1:] if len(cause) > 1 else cause.upper()
            
            master_table.append({
                'Issue': f"#{issue_num}",
                'Type': 'Error',
                'Category': 'Orphan',
                'Member Name': '—',
                'Parent Name': parent_str,
                'Cause': cause,
                'Rows': rows_str
            })
            issue_num += 1
        
        # Parent mismatches
        for mismatch in mismatches:
            # Format member name with alias if it's a numeric ID
            member_name = mismatch["correct_member"]
            member_alias = mismatch["correct_member_alias"]
            if member_alias and str(member_alias) != 'nan':
                if any(char.isdigit() for char in member_name):
                    member_name = f"{member_name} ({member_alias})"
            
            # Parent reference (what children are using)
            parent_ref = mismatch["parent_ref"]
            
            # Cause explanation
            cause = mismatch["cause_explanation"]
            
            # Get all affected child rows
            child_rows = [child['row'] + 2 for child in mismatch['affected_children']]
            rows_str = ', '.join(map(str, sorted(child_rows)))
            
            master_table.append({
                'Issue': f"#{issue_num}",
                'Type': 'Error',
                'Category': 'Parent Mismatch',
                'Member Name': member_name,
                'Parent Name': parent_ref,
                'Cause': cause,
                'Rows': rows_str
            })
            issue_num += 1
        
        # Duplicate errors
        for dup in duplicate_errors:
            excel_rows = [inst['row'] + 2 for inst in dup['instances']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            # Format name with alias if it's a numeric ID
            name = dup["member_name"]
            alias = dup['instances'][0]['alias'] if dup['instances'] else ''
            if alias and str(alias) != 'nan':
                if any(char.isdigit() for char in name):
                    name = f"{name} ({alias})"
            
            master_table.append({
                'Issue': f"#{issue_num}",
                'Type': 'Error',
                'Category': 'Duplicate',
                'Member Name': name,
                'Parent Name': '—',
                'Cause': f'{dup["total_children"]} children (fuzzy)',
                'Rows': rows_str
            })
            issue_num += 1
        
        # Duplicate warnings
        for dup in duplicate_warnings:
            excel_rows = [inst['row'] + 2 for inst in dup['instances']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            # Format name with alias if it's a numeric ID
            name = dup["member_name"]
            alias = dup['instances'][0]['alias'] if dup['instances'] else ''
            if alias and str(alias) != 'nan':
                if any(char.isdigit() for char in name):
                    name = f"{name} ({alias})"
            
            master_table.append({
                'Issue': f"#{issue_num}",
                'Type': 'Warning',
                'Category': 'Duplicate Leaf',
                'Member Name': name,
                'Parent Name': '—',
                'Cause': 'All leaves (acceptable)',
                'Rows': rows_str
            })
            issue_num += 1
        
        # Build sets of rows already flagged - track by column
        flagged_member_column_rows = set()
        flagged_parent_column_rows = set()
        
        # Rows from orphans (parent column flagged)
        for parent_str, data in orphans.items():
            for row in data['rows']:
                flagged_parent_column_rows.add(row)
        
        # Rows from parent mismatches (parent column flagged)
        for mismatch in mismatches:
            for child in mismatch['affected_children']:
                flagged_parent_column_rows.add(child['row'])
        
        # Rows from duplicates (member column flagged)
        for dup in duplicate_errors + duplicate_warnings:
            for inst in dup['instances']:
                flagged_member_column_rows.add(inst['row'])
        
        # Build set of parent names already flagged
        flagged_parent_names = set()
        for parent_str in orphans.keys():
            flagged_parent_names.add(parent_str)
        for mismatch in mismatches:
            if mismatch['is_whitespace']:
                flagged_parent_names.add(mismatch['parent_ref'])
        
        # VENA LENGTH VALIDATION - Check ONLY for 80+ character limit
        vena_length_violations = []
        
        for idx, row in df.iterrows():
            member = str(row['_member_name'])
            parent = str(row['_parent_name']) if pd.notna(row['_parent_name']) else None
            
            excel_row = idx + 2
            
            # Check member length
            if len(member) > 80:
                vena_length_violations.append({
                    'Issue': f"#{issue_num}",
                    'Type': 'Error',
                    'Category': 'Vena Restriction',
                    'Member Name': member,
                    'Parent Name': '—',
                    'Cause': f'Member exceeds 80 chars ({len(member)} chars)',
                    'Rows': str(excel_row)
                })
                issue_num += 1
            
            # Check parent length
            if parent and len(parent) > 80:
                vena_length_violations.append({
                    'Issue': f"#{issue_num}",
                    'Type': 'Error',
                    'Category': 'Vena Restriction',
                    'Member Name': '—',
                    'Parent Name': parent,
                    'Cause': f'Parent exceeds 80 chars ({len(parent)} chars)',
                    'Rows': str(excel_row)
                })
                issue_num += 1
        
        master_table.extend(vena_length_violations)
        
        # Whitespace issues - only if not already flagged
        for ws in whitespace_issues:
            column = ws['column']
            text = ws['text']
            rows = ws['rows']
            cause = ', '.join(ws['issues'])
            
            # Capitalize first letter
            cause = cause[0].upper() + cause[1:] if len(cause) > 1 else cause.upper()
            
            # Filter rows based on column
            if column == '_member_name':
                # Skip if member column already flagged
                unflagged_rows = [r for r in rows if r not in flagged_member_column_rows]
            else:  # _parent_name
                # Skip if parent name already flagged OR if this parent name is in error list
                if text in flagged_parent_names:
                    continue
                unflagged_rows = [r for r in rows if r not in flagged_parent_column_rows]
            
            if unflagged_rows:
                excel_rows = [r + 2 for r in unflagged_rows]
                rows_str = ', '.join(map(str, sorted(excel_rows)))
                
                # Determine member vs parent
                if column == '_member_name':
                    member_name = text
                    parent_name = '—'
                else:
                    member_name = '—'
                    parent_name = text
                
                master_table.append({
                    'Issue': f"#{issue_num}",
                    'Type': 'Warning',
                    'Category': 'Whitespace',
                    'Member Name': member_name,
                    'Parent Name': parent_name,
                    'Cause': f'Both member and parent: {cause}' if member_name != '—' and parent_name != '—' else cause,
                    'Rows': rows_str
                })
                issue_num += 1
        
        # Group by member name for family display
        families = defaultdict(list)
        flagged_member_names = set()
        
        for issue in master_table:
            member = issue['Member Name']
            parent = issue['Parent Name']
            
            # Use member as family key if present
            if member != '—':
                families[member].append(issue)
            elif parent != '—':
                # If no member, use parent as key
                families[parent].append(issue)
            else:
                # Both are blank - standalone issue
                families[f"_standalone_{len(families)}"].append(issue)
            
            # Track flagged names
            if issue['Category'] == 'Whitespace':
                if member != '—':
                    flagged_member_names.add(member)
                if parent != '—':
                    flagged_parent_names.add(parent)
        
        # Build final table with family sub-numbering
        final_table = []
        issue_num = 1
        
        for family_key, issues in families.items():
            if len(issues) == 1:
                # Single issue - no family
                issue = issues[0]
                
                # Filter whitespace warnings for names already flagged
                if issue['Category'] == 'Whitespace':
                    member = issue['Member Name']
                    parent = issue['Parent Name']
                    
                    # Keep primary warnings (both member and parent set)
                    if member != '—' and parent != '—':
                        pass
                    else:
                        # Secondary warning - filter if flagged
                        if member != '—' and (member in flagged_member_names or member in flagged_parent_names):
                            continue
                        if parent != '—' and (parent in flagged_member_names or parent in flagged_parent_names):
                            continue
                
                issue['Issue'] = f"#{issue_num}"
                final_table.append(issue)
                issue_num += 1
            else:
                # Family - multiple issues for same member
                for sub_idx, sub_issue in enumerate(issues, 1):
                    sub_issue['Issue'] = f"#{issue_num}.{sub_idx}"
                    final_table.append(sub_issue)
                
                issue_num += 1
        
        # Display main table
        if final_table:
            df_master = pd.DataFrame(final_table)
            st.dataframe(
                df_master,
                hide_index=True,
                use_container_width=True,
                column_config={
                    'Issue': st.column_config.TextColumn('Issue', width='small'),
                    'Type': st.column_config.TextColumn('Type', width='small'),
                    'Category': st.column_config.TextColumn('Category', width='medium'),
                    'Member Name': st.column_config.TextColumn('Member Name', width='large'),
                    'Parent Name': st.column_config.TextColumn('Parent Name', width='large'),
                    'Cause': st.column_config.TextColumn('Cause', width='medium'),
                    'Rows': st.column_config.TextColumn('Rows', width='medium')
                }
            )
            
            # Whitespace visualization table
            if whitespace_issues:
                st.markdown("---")
                st.markdown("### 🎨 Whitespace Visualization")
                st.markdown("*Background colors highlight whitespace issues in your data*")
                
                # Collect all rows with whitespace issues
                ws_row_set = set()
                for ws in whitespace_issues:
                    ws_row_set.update(ws['rows'])
                
                # Create display data
                ws_display_rows = []
                for row_idx in sorted(ws_row_set):
                    excel_row = row_idx + 2
                    row_data = df.iloc[row_idx]
                    
                    ws_display_rows.append({
                        'Row': excel_row,
                        'Member Name': str(row_data['_member_name']),
                        'Parent Name': str(row_data['_parent_name'])
                    })
                
                if ws_display_rows:
                    df_ws_viz = pd.DataFrame(ws_display_rows)
                    
                    def get_ws_color(text):
                        """Return background color based on whitespace type"""
                        if not text or text == 'nan':
                            return ''
                        
                        # Leading/trailing (CRITICAL - RED)
                        if text != text.strip():
                            return 'background-color: rgba(255, 100, 100, 0.25)'
                        
                        # Double spaces (WARNING - AMBER)
                        if '  ' in text:
                            return 'background-color: rgba(255, 200, 80, 0.25)'
                        
                        # Clean
                        return 'background-color: rgba(100, 255, 100, 0.10)'
                    
                    def style_ws_table(row):
                        return [
                            '',  # Row number - no style
                            get_ws_color(row['Member Name']),
                            get_ws_color(row['Parent Name'])
                        ]
                    
                    styled_df = df_ws_viz.style.apply(style_ws_table, axis=1)
                    
                    # Legend
                    st.markdown("""
                    <div style="display: flex; gap: 20px; margin: 10px 0; font-size: 13px;">
                        <div><span style="background-color: rgba(255,100,100,0.25); padding: 2px 8px; border-radius: 3px;">🔴 Leading/Trailing</span></div>
                        <div><span style="background-color: rgba(255,200,80,0.25); padding: 2px 8px; border-radius: 3px;">🟡 Double Space</span></div>
                        <div><span style="background-color: rgba(100,255,100,0.10); padding: 2px 8px; border-radius: 3px;">✅ Clean</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.dataframe(
                        styled_df,
                        hide_index=True,
                        use_container_width=True,
                        height=400,
                        column_config={
                            'Row': st.column_config.NumberColumn('Row', width='small'),
                            'Member Name': st.column_config.TextColumn('Member Name', width='large'),
                            'Parent Name': st.column_config.TextColumn('Parent Name', width='large')
                        }
                    )
        
        st.markdown('</div>', unsafe_allow_html=True)
