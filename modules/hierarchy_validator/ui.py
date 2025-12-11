"""
Hierarchy Validator Module - UI Layer (v8 Elegant)
Beautiful light-themed presentation with comprehensive validation display
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
        
        uploaded_file = st.file_uploader("Upload parent-child file", type=['xlsx', 'xls', 'csv'], label_visibility="collapsed")
    
    if uploaded_file:
        try:
            # Read file based on type
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Validate required columns
            if '_member_name' not in df.columns or '_parent_name' not in df.columns:
                st.error("Missing required columns: _member_name and _parent_name")
                return
            
            # Show data preview
            st.markdown("---")
            st.markdown(f"**Loaded:** {len(df):,} rows")
            
            # Validate button
            if st.button("Validate Hierarchy", type="primary", use_container_width=True):
                # Run analysis
                with st.spinner("Analyzing..."):
                    orphans = find_orphans(df, max_edit_distance=2)
                    mismatches = find_parent_mismatches(df, max_edit_distance=2)
                    duplicate_errors, duplicate_warnings = find_duplicate_members(df)
                    whitespace_issues = find_whitespace_issues(df)
            
                total_errors = len(orphans) + len(mismatches) + len(duplicate_errors)
                total_warnings = len(duplicate_warnings) + len(whitespace_issues)
                total_issues = total_errors + total_warnings
                
                st.markdown("---")
            
                # Summary badges - 4 pills matching Tree Converter
                if total_errors == 0 and total_warnings == 0:
                    summary_html = '<div style="text-align: center; margin: 20px 0;"><span class="summary-badge badge-success">✓ No issues found</span></div>'
                else:
                    summary_html = f'''
                    <div style="text-align: center; margin: 20px 0;">
                        <span class="summary-badge" style="background: #e3f2fd; color: #1565c0;">{len(df):,} Members Checked</span>
                        <span class="summary-badge" style="background: #e3f2fd; color: #1565c0;">{total_issues} Issues Found</span>
                        <span class="summary-badge badge-warning">{total_warnings} Warnings</span>
                        <span class="summary-badge badge-error">{total_errors} Errors</span>
                    </div>
                    '''
                st.markdown(summary_html, unsafe_allow_html=True)
                
                st.markdown("---")
                
                if total_errors > 0 or total_warnings > 0:
                    # Build master table
                    st.markdown('<div class="results-container">', unsafe_allow_html=True)
                
                    master_table = []
                    issue_num = 1
                
                    # ORPHANS - Most critical! Parent doesn't exist at all
                    for parent_str, data in orphans.items():
                        excel_rows = [r + 2 for r in data['rows']]
                        rows_str = ', '.join(map(str, sorted(excel_rows)))
                    
                        # Build cause explanation (lowercase, will capitalize first letter later)
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
                        excel_row = mismatch['correct_member_row'] + 2
                        num_children = len(mismatch['affected_children'])
                    
                        # Format member name with alias if it's a numeric ID
                        member_name = mismatch["correct_member"]
                        member_alias = mismatch["correct_member_alias"]
                        if member_alias and str(member_alias) != 'nan':
                            if any(char.isdigit() for char in member_name):
                                member_name = f"{member_name} ({member_alias})"
                    
                        # Parent reference (what children are using)
                        parent_ref = mismatch["parent_ref"]
                    
                        # Cause explanation (already properly formatted)
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
                
                    # Whitespace issues - PHASE 2: Only on rows NOT already flagged
                    # Build set of rows already flagged - BUT TRACK WHICH COLUMN!
                    flagged_member_column_rows = set()  # Rows where MEMBER column is flagged
                    flagged_parent_column_rows = set()  # Rows where PARENT column is flagged
                
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
                
                    # Build set of parent names already flagged with issues
                    flagged_parent_names = set()
                
                    # Parent names from orphans
                    for parent_str in orphans.keys():
                        flagged_parent_names.add(parent_str)
                
                    # Parent names from mismatches with whitespace
                    for mismatch in mismatches:
                        if mismatch['is_whitespace']:
                            flagged_parent_names.add(mismatch['parent_ref'])
                
                    # VENA VALIDATION - Check ONLY for 80+ character limit
                    # (Leading/trailing/tabs are now integrated into orphan/mismatch/whitespace logic)
                    vena_length_violations = []
                
                    for idx, row in df.iterrows():
                        member = str(row['_member_name'])
                        parent = str(row['_parent_name'])
                        row_num = idx + 2  # Excel row (1-indexed + header)
                    
                        # Check member name length
                        if member and member != 'nan' and len(member) > 80:
                            vena_length_violations.append({
                                'row': row_num,
                                'column': 'Member',
                                'name': member,
                                'length': len(member)
                            })
                    
                        # Check parent name length
                        if parent and parent != 'nan' and len(parent) > 80:
                            vena_length_violations.append({
                                'row': row_num,
                                'column': 'Parent',
                                'name': parent,
                                'length': len(parent)
                            })
                
                    # Group whitespace issues by text to find duplicates across columns
                    from collections import defaultdict
                    ws_grouped = defaultdict(lambda: {'member_rows': [], 'parent_rows': [], 'issues': [], 'alias': ''})
                
                    for ws in whitespace_issues:
                        # Skip if this is a _parent_name already caught in orphans or mismatches
                        if ws['column'] == '_parent_name' and ws['text'] in flagged_parent_names:
                            continue
                    
                        # Filter based on WHICH COLUMN is being checked
                        if ws['column'] == '_member_name':
                            # Check if MEMBER column is flagged for these rows
                            unflagged_rows = [r for r in ws['rows'] if r not in flagged_member_column_rows]
                        else:  # _parent_name
                            # Check if PARENT column is flagged for these rows
                            unflagged_rows = [r for r in ws['rows'] if r not in flagged_parent_column_rows]
                    
                        if not unflagged_rows:
                            continue
                    
                        text = ws['highlighted']
                    
                        if ws['column'] == '_member_name':
                            ws_grouped[text]['member_rows'].extend(unflagged_rows)
                        else:
                            ws_grouped[text]['parent_rows'].extend(unflagged_rows)
                    
                        ws_grouped[text]['issues'] = ws['issues']
                        ws_grouped[text]['alias'] = ws['alias_example']
                
                    # Now create merged entries
                    for text, data in ws_grouped.items():
                        member_rows = sorted(data['member_rows'])
                        parent_rows = sorted(data['parent_rows'])
                    
                        # Format name with alias if numeric
                        name = text
                        alias = data['alias']
                        if alias and str(alias) != 'nan':
                            if any(char.isdigit() for char in text):
                                name = f"{text} ({alias})"
                            else:
                                name = text
                    
                        # Determine if both columns or just one
                        if member_rows and parent_rows:
                            # Both columns have the issue - MERGE!
                            all_rows = sorted(set(member_rows + parent_rows))
                            excel_rows = [r + 2 for r in all_rows]
                            rows_str = ', '.join(map(str, excel_rows))
                        
                            issue_text = ', '.join(data['issues'])
                            cause = f"Both member and parent: {issue_text}"
                        
                            master_table.append({
                                'Issue': f"#{issue_num}",
                                'Type': 'Warning',
                                'Category': 'Whitespace',
                                'Member Name': name,
                                'Parent Name': name,
                                'Cause': cause,
                                'Rows': rows_str
                            })
                            issue_num += 1
                        
                        elif member_rows:
                            # Only member column
                            excel_rows = [r + 2 for r in member_rows]
                            rows_str = ', '.join(map(str, excel_rows))
                        
                            issue_text = ', '.join(data['issues'])
                            cause = f"Member name: {issue_text}"
                        
                            master_table.append({
                                'Issue': f"#{issue_num}",
                                'Type': 'Warning',
                                'Category': 'Whitespace',
                                'Member Name': name,
                                'Parent Name': '—',
                                'Cause': cause,
                                'Rows': rows_str
                            })
                            issue_num += 1
                        
                        elif parent_rows:
                            # Only parent column
                            excel_rows = [r + 2 for r in parent_rows]
                            rows_str = ', '.join(map(str, excel_rows))
                        
                            issue_text = ', '.join(data['issues'])
                            cause = f"Parent name: {issue_text}"
                        
                            master_table.append({
                                'Issue': f"#{issue_num}",
                                'Type': 'Warning',
                                'Category': 'Whitespace',
                                'Member Name': '—',
                                'Parent Name': name,
                                'Cause': cause,
                                'Rows': rows_str
                            })
                            issue_num += 1
                
                    # Add Vena 80+ character violations
                    if vena_length_violations:
                        # Group by row to combine member and parent violations
                        from collections import defaultdict
                        vena_by_row = defaultdict(lambda: {'member_name': '', 'member_len': 0, 'parent_name': '', 'parent_len': 0})
                    
                        for v in vena_length_violations:
                            row = v['row']
                            if v['column'] == 'Member':
                                vena_by_row[row]['member_name'] = v['name']
                                vena_by_row[row]['member_len'] = v['length']
                            else:
                                vena_by_row[row]['parent_name'] = v['name']
                                vena_by_row[row]['parent_len'] = v['length']
                    
                        for row, data in sorted(vena_by_row.items()):
                            causes = []
                            if data['member_name']:
                                causes.append(f"Member exceeds 80 chars ({data['member_len']} chars)")
                            if data['parent_name']:
                                causes.append(f"Parent exceeds 80 chars ({data['parent_len']} chars)")
                        
                            master_table.append({
                                'Issue': f"#{issue_num}",
                                'Type': 'Error',
                                'Category': 'Vena Restriction',
                                'Member Name': data['member_name'] if data['member_name'] else '—',
                                'Parent Name': data['parent_name'] if data['parent_name'] else '—',
                                'Cause': '; '.join(causes),
                                'Rows': str(row)
                            })
                            issue_num += 1
                
                    # Display master table with family grouping
                    if master_table:
                        # Group issues by member name to find families
                        from collections import defaultdict
                        families = defaultdict(list)
                    
                        for idx, issue in enumerate(master_table):
                            member_name = issue['Member Name']
                            # Skip orphans (no member name)
                            if member_name == '—':
                                families[f"_single_{idx}"] = [issue]
                            else:
                                families[member_name].append(issue)
                    
                        # Track ALL flagged names (both as members and as parents)
                        flagged_member_names = set()  # Names that appear as members in errors/families
                        flagged_parent_names = set()  # Names that appear as parents in errors/families
                    
                        # First pass: identify families and collect ALL names from family items
                        for member_name, issues in families.items():
                            if len(issues) >= 2 and not member_name.startswith('_single_'):
                                # This is a family - flag the member name
                                flagged_member_names.add(member_name)
                            
                                # Also flag parent names from ALL items in the family (errors and warnings)
                                for issue in issues:
                                    if issue['Parent Name'] != '—':
                                        flagged_parent_names.add(issue['Parent Name'])
                    
                        # Second pass: collect names from ALL errors
                        for issue in master_table:
                            if issue['Type'] == 'Error':
                                member = issue['Member Name']
                                parent = issue['Parent Name']
                            
                                if member != '—':
                                    flagged_member_names.add(member)
                                if parent != '—':
                                    flagged_parent_names.add(parent)
                    
                        # Third pass: flag names from "primary" whitespace warnings (both member and parent set)
                        # These are the main warnings; parent-only warnings are secondary
                        for issue in master_table:
                            if issue['Category'] == 'Whitespace':
                                member = issue['Member Name']
                                parent = issue['Parent Name']
                            
                                # If both are set, this is a primary warning - flag both names
                                if member != '—' and parent != '—':
                                    flagged_member_names.add(member)
                                    flagged_parent_names.add(parent)
                    
                        # Build final table with family sub-numbering (no header rows)
                        final_table = []
                        issue_num = 1
                    
                        for family_key, issues in families.items():
                            if len(issues) == 1:
                                # Single issue - no family
                                issue = issues[0]
                            
                                # Filter out whitespace warnings for names already flagged
                                if issue['Category'] == 'Whitespace':
                                    member = issue['Member Name']
                                    parent = issue['Parent Name']
                                
                                    # Don't filter primary warnings (both member and parent set)
                                    # These are standalone data quality issues, not duplicates
                                    if member != '—' and parent != '—':
                                        # This is a primary warning - keep it
                                        pass
                                    else:
                                        # This is a secondary warning (member-only or parent-only)
                                        # Filter if the name is already flagged
                                        if member != '—' and (member in flagged_member_names or member in flagged_parent_names):
                                            continue  # Skip - member already flagged
                                    
                                        if parent != '—' and (parent in flagged_member_names or parent in flagged_parent_names):
                                            continue  # Skip - parent already flagged
                            
                                issue['Issue'] = f"#{issue_num}"
                                final_table.append(issue)
                                issue_num += 1
                            else:
                                # FAMILY - multiple issues for same member
                                # NO HEADER ROW - just show sub-numbered items with member name
                                for sub_idx, sub_issue in enumerate(issues, 1):
                                    sub_issue['Issue'] = f"#{issue_num}.{sub_idx}"
                                    # Keep member name visible in all rows
                                    final_table.append(sub_issue)
                            
                                issue_num += 1
                    
                        df_master = pd.DataFrame(final_table)
                        st.dataframe(
                            df_master,
                            hide_index=True,
                            width='stretch',
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
                    
                        # WHITESPACE VISUALIZATION TABLE - Modern & Beautiful
                        if whitespace_issues:
                            st.markdown("---")
                            st.markdown("### Whitespace Visualization")
                            st.markdown("*Background colors highlight whitespace issues in your data*")
                        
                            # Build a styled dataframe with all rows that have whitespace issues
                            ws_display_rows = []
                        
                            # Collect all rows with whitespace issues
                            ws_row_set = set()
                            for ws in whitespace_issues:
                                ws_row_set.update(ws['rows'])
                        
                            # Create display data
                            for row_idx in sorted(ws_row_set):
                                excel_row = row_idx + 2
                                row_data = df.iloc[row_idx]
                            
                                member_name = str(row_data['_member_name'])
                                parent_name = str(row_data['_parent_name'])
                            
                                ws_display_rows.append({
                                    'Row': excel_row,
                                    'Member Name': member_name,
                                    'Parent Name': parent_name
                                })
                        
                            if ws_display_rows:
                                df_ws_viz = pd.DataFrame(ws_display_rows)
                            
                                # Function to detect whitespace type
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
                            
                                # Apply styling
                                def style_ws_table(row):
                                    member_style = get_ws_color(row['Member Name'])
                                    parent_style = get_ws_color(row['Parent Name'])
                                
                                    return [
                                        '',  # Row number - no style
                                        member_style,
                                        parent_style
                                    ]
                            
                                styled_df = df_ws_viz.style.apply(style_ws_table, axis=1)
                            
                                # Add legend
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
                                    width='stretch',
                                    height=400,
                                    column_config={
                                        'Row': st.column_config.NumberColumn('Row', width='small'),
                                        'Member Name': st.column_config.TextColumn('Member Name', width='large'),
                                        'Parent Name': st.column_config.TextColumn('Parent Name', width='large')
                                    }
                                )
                
                    st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")



