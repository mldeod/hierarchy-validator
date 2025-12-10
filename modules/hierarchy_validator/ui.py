"""
Hierarchy Validator Module - UI Layer
Validate parent-child hierarchies with comprehensive error detection
"""

import streamlit as st
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import validation engine
from modules.hierarchy_validator.validation_engine import (
    find_orphans,
    find_parent_mismatches,
    find_duplicate_members,
    find_whitespace_issues
)

def render(workflow_data=None):
    """
    Render the Hierarchy Validator module
    
    Args:
        workflow_data: DataFrame passed from another module (optional)
    """
    
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
    
    # Initialize session state
    if 'validator_results' not in st.session_state:
        st.session_state.validator_results = None
    if 'validator_file_key' not in st.session_state:
        st.session_state.validator_file_key = 0
    if 'validator_workflow_data' not in st.session_state:
        st.session_state.validator_workflow_data = None
    
    # Store workflow data in session state on first load
    if workflow_data is not None and st.session_state.validator_workflow_data is None:
        st.session_state.validator_workflow_data = workflow_data.copy()
    
    # Determine data source
    df = None
    data_source = None
    
    # Check session state first
    if st.session_state.validator_workflow_data is not None:
        df = st.session_state.validator_workflow_data
        data_source = "workflow"
        st.markdown("""
        <div class="success-box">
            <h3>✓ Data Received from Tree Converter</h3>
            <p>Your converted hierarchy has been automatically loaded and is ready to validate.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # File upload
        st.markdown("---")
        uploaded_file = st.file_uploader(
            "Upload Hierarchy File",
            type=['xlsx', 'xls', 'csv'],
            help="Upload your parent-child hierarchy file (CSV or Excel)",
            key=f"validator_upload_{st.session_state.validator_file_key}"
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                data_source = "upload"
                st.success(f"File loaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
                return
    
    # Process data if available
    if df is not None:
        
        # Validate required columns
        if '_member_name' not in df.columns or '_parent_name' not in df.columns:
            st.error("❌ Missing required columns: _member_name and _parent_name")
            st.info("Expected columns: _dim, _member_name, _member_alias, _parent_name, _operator, _cmd")
            return
        
        # Show data preview
        st.markdown("---")
        st.markdown("#### Data Preview")
        st.dataframe(df.head(10), width="stretch")
        
        st.markdown(f"""
        <div class="tip-box">
            <small><strong>Loaded:</strong> {len(df):,} rows × {len(df.columns)} columns</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Validate button
        if st.button("Validate Hierarchy", type="primary", width="stretch", key="validator_run"):
            with st.spinner('Running validation checks...'):
                
                # Run all validation checks
                orphans = find_orphans(df, max_edit_distance=2)
                mismatches = find_parent_mismatches(df, max_edit_distance=2)
                duplicate_errors, duplicate_warnings = find_duplicate_members(df)
                whitespace_issues = find_whitespace_issues(df)
                
                # Check Vena length restrictions
                vena_length_violations = []
                for idx, row in df.iterrows():
                    member = str(row['_member_name'])
                    parent = str(row['_parent_name'])
                    
                    if len(member) > 80:
                        vena_length_violations.append({
                            'row': idx,
                            'column': '_member_name',
                            'value': member,
                            'length': len(member)
                        })
                    if len(parent) > 80:
                        vena_length_violations.append({
                            'row': idx,
                            'column': '_parent_name', 
                            'value': parent,
                            'length': len(parent)
                        })
                
                # Store results
                st.session_state.validator_results = {
                    'orphans': orphans,
                    'mismatches': mismatches,
                    'duplicate_errors': duplicate_errors,
                    'duplicate_warnings': duplicate_warnings,
                    'whitespace_issues': whitespace_issues,
                    'vena_length_violations': vena_length_violations,
                    'df': df
                }
        
        # Display results if available
        if st.session_state.validator_results is not None:
            results = st.session_state.validator_results
            
            orphans = results['orphans']
            mismatches = results['mismatches']
            duplicate_errors = results['duplicate_errors']
            duplicate_warnings = results['duplicate_warnings']
            whitespace_issues = results['whitespace_issues']
            vena_length_violations = results['vena_length_violations']
            
            total_errors = len(orphans) + len(mismatches) + len(duplicate_errors) + len(vena_length_violations)
            total_warnings = len(duplicate_warnings) + len(whitespace_issues)
            
            st.markdown("---")
            st.markdown("#### Validation Results")
            
            # Summary badges
            if total_errors == 0 and total_warnings == 0:
                st.markdown("""
                <div class="success-box">
                    <h2 style="margin: 0;">✓ Perfect Hierarchy!</h2>
                    <p style="margin: 10px 0 0 0;">No errors or warnings found. Your hierarchy is ready for Vena import.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2 style="color: {'#ff3b30' if total_errors > 0 else '#34c759'}; margin: 0;">{total_errors}</h2>
                        <p style="margin: 5px 0 0 0; color: #6e6e73;">Errors</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2 style="color: {'#ff9500' if total_warnings > 0 else '#34c759'}; margin: 0;">{total_warnings}</h2>
                        <p style="margin: 5px 0 0 0; color: #6e6e73;">Warnings</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h2 style="color: #0051D5; margin: 0;">{len(df):,}</h2>
                        <p style="margin: 5px 0 0 0; color: #6e6e73;">Total Members</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Build master issue table
                master_table = []
                issue_num = 1
                
                # ORPHANS
                for parent_str, data in orphans.items():
                    excel_rows = [r + 2 for r in data['rows']]
                    rows_str = ', '.join(map(str, sorted(excel_rows)))
                    
                    cause = "Parent doesn't exist as member"
                    if data['has_whitespace']:
                        cause += " (has whitespace)"
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Error',
                        'Category': 'Orphan',
                        'Member': '—',
                        'Parent': parent_str,
                        'Cause': cause,
                        'Rows': rows_str
                    })
                    issue_num += 1
                
                # PARENT MISMATCHES
                for mismatch in mismatches:
                    member_name = mismatch["correct_member"]
                    member_alias = mismatch.get("correct_member_alias", "")
                    
                    if member_alias and str(member_alias) != 'nan':
                        if any(char.isdigit() for char in member_name):
                            member_name = f"{member_name} ({member_alias})"
                    
                    parent_ref = mismatch["parent_ref"]
                    cause = mismatch.get("cause_explanation", "Name mismatch")
                    
                    child_rows = [child['row'] + 2 for child in mismatch['affected_children']]
                    rows_str = ', '.join(map(str, sorted(child_rows)))
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Error',
                        'Category': 'Mismatch',
                        'Member': member_name,
                        'Parent': parent_ref,
                        'Cause': cause,
                        'Rows': rows_str
                    })
                    issue_num += 1
                
                # DUPLICATE ERRORS
                for dup in duplicate_errors:
                    excel_rows = [inst['row'] + 2 for inst in dup['instances']]
                    rows_str = ', '.join(map(str, sorted(excel_rows)))
                    
                    name = dup["member_name"]
                    alias = dup['instances'][0].get('alias', '') if dup['instances'] else ''
                    if alias and str(alias) != 'nan':
                        if any(char.isdigit() for char in name):
                            name = f"{name} ({alias})"
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Error',
                        'Category': 'Duplicate',
                        'Member': name,
                        'Parent': '—',
                        'Cause': f'{dup.get("total_children", 0)} children',
                        'Rows': rows_str
                    })
                    issue_num += 1
                
                # VENA LENGTH VIOLATIONS
                for violation in vena_length_violations:
                    excel_row = violation['row'] + 2
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Error',
                        'Category': 'Vena Limit',
                        'Member': violation['value'][:50] + '...',
                        'Parent': '—',
                        'Cause': f'{violation["length"]} chars (max 80)',
                        'Rows': str(excel_row)
                    })
                    issue_num += 1
                
                # DUPLICATE WARNINGS
                for dup in duplicate_warnings:
                    excel_rows = [inst['row'] + 2 for inst in dup['instances']]
                    rows_str = ', '.join(map(str, sorted(excel_rows)))
                    
                    name = dup["member_name"]
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Warning',
                        'Category': 'Duplicate Leaf',
                        'Member': name,
                        'Parent': '—',
                        'Cause': 'All leaves (acceptable)',
                        'Rows': rows_str
                    })
                    issue_num += 1
                
                # WHITESPACE ISSUES
                for issue in whitespace_issues:
                    rows_str = ', '.join(map(str, [r + 2 for r in issue['rows']]))
                    
                    master_table.append({
                        'Issue': f"#{issue_num}",
                        'Type': 'Warning',
                        'Category': 'Whitespace',
                        'Member': issue.get('member_name', '—'),
                        'Parent': '—',
                        'Cause': ', '.join(issue['issues']),
                        'Rows': rows_str
                    })
                    issue_num += 1
                
                # Display master table
                if master_table:
                    st.markdown("---")
                    st.markdown("#### Issues Found")
                    
                    issues_df = pd.DataFrame(master_table)
                    st.dataframe(issues_df, width="stretch", height=400)
                    
                    # Download button for issues
                    csv = issues_df.to_csv(index=False)
                    st.download_button(
                        label="Download Issues Report (CSV)",
                        data=csv,
                        file_name="hierarchy_issues_report.csv",
                        mime="text/csv",
                        key="validator_download_issues"
                    )
                
                # Summary
                st.markdown("---")
                if total_errors > 0:
                    st.markdown(f"""
                    <div class="error-box">
                        <h3>Action Required</h3>
                        <p>Found <strong>{total_errors} errors</strong> that must be fixed before importing to Vena.</p>
                        <p>Review the issues table above and correct the data in your source file.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>Ready to Import</h3>
                        <p>No errors found! Your hierarchy is ready for Vena.</p>
                        {f'<p><small>Note: {total_warnings} warnings detected but these won\'t prevent import.</small></p>' if total_warnings > 0 else ''}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Clear button
            if st.button("Clear Results and Load New File", width="stretch", key="validator_clear"):
                st.session_state.validator_results = None
                st.session_state.validator_workflow_data = None
                st.session_state.validator_file_key += 1
                st.rerun()
    
    else:
        # No data loaded
        st.markdown("""
        <div class="tip-box">
            <small><strong>Tip:</strong> You can send data directly from the Tree Converter, or upload your own parent-child file here!</small>
        </div>
        """, unsafe_allow_html=True)
