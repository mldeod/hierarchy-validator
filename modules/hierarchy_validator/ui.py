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
    find_whitespace_issues,
    find_whitespace_issues_detailed
)

# Import family grouping module (Item 3 - Family Grouping Logic)
from modules.hierarchy_validator.issue_family_grouping import (
    collect_all_issues,
    group_issues_by_family,
    assign_family_numbers,
    build_master_table
)

from shared.tooltip_helper import (
    create_tooltip,
    TOOLTIPS, 
    get_info_circle_icon,
    get_error_icon,
    get_warning_icon,
    get_info_icon
)


def render(workflow_data=None):
    # File upload or workflow data
    if workflow_data is not None:
        df = workflow_data
        uploaded_file = None
    else:
        st.markdown("### Validate Parent-Child Hierarchy")
        
        # Inline help - short version with tight bullet spacing
        with st.expander("What does this validate?", expanded=False):
            st.markdown("""
            Validates parent-child hierarchies for platform import, checking for:
            
            - Missing parents ➞ orphaned members
            - Name mismatches ➞ typos
            - Duplicate member names
            - Whitespace ➞ formatting issues
            - Platform naming restrictions
            
            **Required format:** CSV or Excel with `_member_name` and `_parent_name` columns
            
            **Fix guidance:** Errors must be resolved before import. Warnings should be reviewed.
            """)
        
        uploaded_file = st.file_uploader(
            "Upload Parent-Child File",
            type=['xlsx', 'xls', 'csv'],
            help="Upload your CSV or Excel file with _member_name and _parent_name columns",
            key='hierarchy_file_uploader'
        )

        if uploaded_file:
            # AUDITOR PATTERN: Clear validation state on new file upload
            # Check if file changed by comparing with stored file name
            if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
                st.session_state.last_uploaded_file = uploaded_file.name
                # Clear previous validation results
                if 'validation_results' in st.session_state:
                    del st.session_state.validation_results
            
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
                        orphan_errors, orphan_warnings = find_orphans(df, max_edit_distance=2)
                        mismatches = find_parent_mismatches(df, max_edit_distance=2)
                        duplicate_errors, duplicate_warnings = find_duplicate_members(df)
                        whitespace_issues = find_whitespace_issues(df)
            
                    # AUDITOR PATTERN: Promote validation results to Session State
                    # "Data must outlive the interaction"
                    st.session_state.validation_results = {
                        'df': df,
                        'orphan_errors': orphan_errors,
                        'orphan_warnings': orphan_warnings,
                        'mismatches': mismatches,
                        'duplicate_errors': duplicate_errors,
                        'duplicate_warnings': duplicate_warnings,
                        'whitespace_issues': whitespace_issues,
                        'total_errors': len(orphan_errors) + len(mismatches) + len(duplicate_errors),
                        'total_warnings': len(orphan_warnings) + len(duplicate_warnings) + len(whitespace_issues),
                        'total_issues': len(orphan_errors) + len(mismatches) + len(duplicate_errors) + len(orphan_warnings) + len(duplicate_warnings) + len(whitespace_issues)
                    }
                
                # AUDITOR PATTERN: Display results if they exist in session state
                # Decouple Action (button) from Display (data present)
                if 'validation_results' in st.session_state:
                    # Extract from session state
                    results = st.session_state.validation_results
                    df = results['df']
                    orphan_errors = results['orphan_errors']
                    orphan_warnings = results['orphan_warnings']
                    mismatches = results['mismatches']
                    duplicate_errors = results['duplicate_errors']
                    duplicate_warnings = results['duplicate_warnings']
                    whitespace_issues = results['whitespace_issues']
                    total_errors = results['total_errors']
                    total_warnings = results['total_warnings']
                    total_issues = results['total_issues']
                    
                    st.markdown("---")
            
                    # Statistics Pills - Phase 2 Iteration 1 - OPTION D
                    # Styling: shared/styling.py (DRY compliance)
                    # Distribution: space-evenly for balanced layout
                    if total_errors == 0 and total_warnings == 0:
                        summary_html = '<div style="text-align: center; margin: 20px 0;"><span class="summary-badge badge-success">✓ No issues found</span></div>'
                    else:
                        summary_html = f'''
                        <div style="display: flex; justify-content: space-evenly; margin: 20px 0;">
                            <span class="summary-badge">{len(df):,} Members Checked</span>
                            <span class="summary-badge">{total_issues} Issues Found</span>
                            <span class="summary-badge badge-warning">{total_warnings} Warnings</span>
                            <span class="summary-badge badge-error">{total_errors} Errors</span>
                        </div>
                        '''
                    st.markdown(summary_html, unsafe_allow_html=True)
                
                    if total_errors > 0 or total_warnings > 0:
                        # Build master table
                        st.markdown('<div class="results-container">', unsafe_allow_html=True)
                
                        # ============================================================
                        # FAMILY-BASED ISSUE GROUPING (Item 3 - Refactored)
                        # ============================================================
                        # Business Rule: All issues for the same logical member
                        # (after whitespace normalization) are grouped under ONE
                        # family number, regardless of issue type.
                        #
                        # Architecture: 4-Layer Modular Design
                        # 1. Collect: Gather all issues from validation results
                        # 2. Group: Group by cleaned member name
                        # 3. Number: Assign family numbers (#N or #N.1, #N.2)
                        # 4. Build: Format for table output
                        # ============================================================
                        
                        # Prepare whitespace_grouped dict for collection
                        # (This section handles filtering and grouping whitespace issues)
                        from collections import defaultdict
                        
                        # Build set of rows already flagged - BUT TRACK WHICH COLUMN!
                        flagged_member_column_rows = set()
                        flagged_parent_column_rows = set()
                        
                        # Rows from orphan errors (parent column flagged)
                        for parent_str, data in orphan_errors.items():
                            for row in data['rows']:
                                flagged_parent_column_rows.add(row)
                        
                        # Rows from orphan warnings (parent column flagged)
                        for parent_str, data in orphan_warnings.items():
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
                        
                        # Parent names from orphan errors
                        for parent_str in orphan_errors.keys():
                            flagged_parent_names.add(parent_str)
                        
                        # Parent names from orphan warnings
                        for parent_str in orphan_warnings.keys():
                            flagged_parent_names.add(parent_str)
                        
                        # Parent names from mismatches with whitespace
                        for mismatch in mismatches:
                            if mismatch['is_whitespace']:
                                flagged_parent_names.add(mismatch['parent_ref'])
                        
                        # Group whitespace issues by text to find duplicates across columns
                        ws_grouped = defaultdict(lambda: {'member_rows': [], 'parent_rows': [], 'issues': [], 'alias': ''})
                        
                        for ws in whitespace_issues:
                            # Skip if this is a _parent_name already caught in orphans or mismatches
                            if ws['column'] == '_parent_name' and ws['text'] in flagged_parent_names:
                                continue
                            
                            # Filter based on WHICH COLUMN is being checked
                            if ws['column'] == '_member_name':
                                unflagged_rows = [r for r in ws['rows'] if r not in flagged_member_column_rows]
                            else:  # _parent_name
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
                        
                        # Collect Vena length violations
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
                        
                        # Now use the new modular approach
                        all_issues = collect_all_issues(
                            orphan_errors, orphan_warnings, mismatches,
                            duplicate_errors, duplicate_warnings,
                            ws_grouped, vena_length_violations, df
                        )
                        
                        families = group_issues_by_family(all_issues)
                        numbered_issues = assign_family_numbers(families)
                        master_table = build_master_table(numbered_issues)
                        
                        # Display master table with family grouping
                        if master_table:
                            # ================================================================
                            # DISPLAY FILTERING LOGIC
                            # ================================================================
                            # Purpose: Filter redundant whitespace warnings for cleaner UI
                            # - If a member has an ERROR, don't also show whitespace WARNING
                            # - Reduces noise, shows only primary issues
                            # 
                            # Note: master_table already has CORRECT family numbers from
                            # issue_family_grouping module. We preserve those numbers!
                            # ================================================================
                            
                            from collections import defaultdict
                            from .issue_family_grouping import clean_name  # Import from module (DRY!)
                            
                            # Build map of all cleaned member names in the file
                            member_name_map = {}  # cleaned_name → actual_member_name
                            for issue in master_table:
                                if issue['Member Name'] != '—':
                                    cleaned = clean_name(issue['Member Name'])
                                    if cleaned and cleaned not in member_name_map:
                                        # Use the first (cleanest) version as canonical
                                        member_name_map[cleaned] = issue['Member Name']
                            
                            # Group issues by their LOGICAL grouping key
                            # NOTE: We group for FILTERING purposes only, NOT for numbering!
                            # The Issue numbers from master_table are PRESERVED!
                            families = defaultdict(list)
                            
                            for issue in master_table:
                                member_name = issue['Member Name']
                                category = issue['Category']
                                
                                # ALWAYS clean grouping keys (fixes the Parent Mismatch bug!)
                                # All categories use the same logic now
                                if member_name != '—':
                                    # Use cleaned member name
                                    grouping_key = clean_name(member_name) or member_name
                                else:
                                    # Orphan - try to match with existing member by cleaned parent
                                    parent_cleaned = clean_name(issue['Parent Name'])
                                    if parent_cleaned and parent_cleaned in member_name_map:
                                        # Found matching member! Group with it
                                        grouping_key = parent_cleaned
                                    else:
                                        # True orphan - group by parent
                                        grouping_key = f"_orphan_{parent_cleaned or issue['Parent Name']}"
                                
                                families[grouping_key].append(issue)
                            
                            # ================================================================
                            # STEP 1: Track flagged names and build final table
                            # ================================================================
                    
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
                    
                            # Build final table with filtering (PRESERVE Issue numbers!)
                            # Note: master_table already has correct family numbers from our module
                            # We only apply filtering here, NOT re-numbering!
                            final_table = []
                    
                            for family_key, issues in families.items():
                                # Apply filtering logic for each issue in the family
                                for issue in issues:
                                    # Filter out whitespace warnings for names already flagged
                                    if issue['Category'] == 'Whitespace':
                                        member = issue['Member Name']
                                        parent = issue['Parent Name']
                                
                                        # Don't filter primary warnings (both member and parent set)
                                        # These are standalone data quality issues, not duplicates
                                        if member != '—' and parent != '—':
                                            # This is a primary warning - keep it
                                            final_table.append(issue)  # ← Preserve Issue number!
                                        else:
                                            # This is a secondary warning (member-only or parent-only)
                                            # Filter if the name is already flagged
                                            if member != '—' and (member in flagged_member_names or member in flagged_parent_names):
                                                continue  # Skip - member already flagged
                                    
                                            if parent != '—' and (parent in flagged_member_names or parent in flagged_parent_names):
                                                continue  # Skip - parent already flagged
                                            
                                            # Not filtered - keep it
                                            final_table.append(issue)  # ← Preserve Issue number!
                                    else:
                                        # Not a whitespace warning - always keep it
                                        final_table.append(issue)  # ← Preserve Issue number!
                    
                            df_master = pd.DataFrame(final_table)
                            
                            # Reorder columns to put Issue first (left-most)
                            column_order = ['Issue', 'Type', 'Category', 'Member Name', 'Parent Name', 'Cause', 'Rows']
                            df_master = df_master[column_order]
                            
                            # AUDITOR RECOMMENDATION (Item 3 - Fix 2):
                            # Ensure row height accommodates wrapped issue lists
                            # (e.g., "#5.1, #5.2, #5.3, #5.4, #5.5" in 300px column)
                            # Use column_config to ensure proper text wrapping and readability
                            st.dataframe(
                                df_master,
                                hide_index=True,
                                width='stretch',
                                column_config={
                                    'Issue': st.column_config.TextColumn(
                                        'Issue',
                                        width='small',
                                        help='Family number (e.g., #5.1, #5.2)'
                                    ),
                                    'Type': st.column_config.TextColumn(
                                        'Type',
                                        width='small'
                                    ),
                                    'Category': st.column_config.TextColumn(
                                        'Category',
                                        width='medium'
                                    ),
                                    'Member Name': st.column_config.TextColumn(
                                        'Member Name',
                                        width='large'
                                    ),
                                    'Parent Name': st.column_config.TextColumn(
                                        'Parent Name',
                                        width='large'
                                    ),
                                    'Cause': st.column_config.TextColumn(
                                        'Cause',
                                        width='large'
                                    ),
                                    'Rows': st.column_config.TextColumn(
                                        'Rows',
                                        width='medium',
                                        help='Excel row numbers'
                                    )
                                },
                                height=400  # Fixed height with scrolling for better UX
                            )
                    
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                        # ================================================================
                        # FIXABLE ISSUES SECTION - Single Source of Truth Architecture
                        # ================================================================
                        # Extract fixable issues FROM final_table (already built, numbered, grouped)
                        # Categories that are fixable: Whitespace, Parent Mismatch
                        
                        fixable_issues = [
                            issue for issue in final_table 
                            if issue['Category'] in ['Whitespace', 'Parent Mismatch']
                        ]
                        
                        if fixable_issues:
                            from . import fixable_issues_visualizer
                            fixable_issues_visualizer.render_fixable_section(
                                fixable_issues=fixable_issues,
                                df=df
                            )
        
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
        else:
            # Show template download when no file
            st.markdown("#### Need a Template?")
            st.markdown("""
            <div class="template-info-box">
                Download our sample template to see the expected format for parent-child hierarchies:
            </div>
            """, unsafe_allow_html=True)
            
            try:
                # Get template from this module's templates folder
                import os
                module_dir = os.path.dirname(os.path.abspath(__file__))
                template_path = os.path.join(module_dir, 'templates', 'sample_template.csv')
                
                with open(template_path, 'rb') as f:
                    st.download_button(
                        label="Download Sample Template",
                        data=f,
                        file_name="hierarchy_validator_sample_template.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="validator_sample_download"
                    )
            except:
                st.info("Sample template will be available after setup")



