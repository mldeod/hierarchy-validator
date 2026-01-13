"""
Issue Family Grouping Module
Handles family-based grouping and numbering of validation issues

Business Rule: All issues for the same logical member (after whitespace 
normalization) should be grouped under ONE family number, regardless of 
issue type (Parent Mismatch, Whitespace, Duplicate, etc.).

Architecture: 4-Layer Modular Design
1. Normalization Layer: clean_name()
2. Collection Layer: collect_all_issues()
3. Grouping Layer: group_issues_by_family() + get_family_key()
4. Numbering Layer: assign_family_numbers() + build_master_table()

Created: January 11, 2026
Lab of Possibilities - Hierarchy Validator
"""

from collections import defaultdict


# ============================================================================
# LAYER 1: NORMALIZATION
# ============================================================================

def clean_name(name):
    """
    Normalize whitespace in member/parent names for grouping
    
    This is the CANONICAL whitespace normalization function.
    Used everywhere for consistency (DRY principle).
    
    Normalization Rules:
    1. Strip leading/trailing whitespace
    2. Replace tabs with spaces
    3. Collapse multiple spaces to single space
    
    Args:
        name: String (member or parent name)
    
    Returns:
        String with normalized whitespace, or None if invalid
    
    Examples:
        "Net revenue  - Audit" → "Net revenue - Audit"
        " Marketing\t" → "Marketing"
        "  Costs  and  expenses  " → "Costs and expenses"
        "" → None
        "—" → None
    """
    if not name or name == '—':
        return None
    
    # Strip, replace tabs, collapse double spaces
    normalized = name.strip().replace('\t', ' ')
    
    # Collapse multiple consecutive spaces to single space
    while '  ' in normalized:
        normalized = normalized.replace('  ', ' ')
    
    return normalized


def get_family_key(issue):
    """
    Determine the family grouping key for an issue
    
    Business Rules:
    - If Member Name exists (not '—'): Use clean_name(Member Name)
    - If Member Name is '—' (Orphan): Use clean_name(Parent Name) with prefix
    
    This ensures all issues for the same logical member (after whitespace
    normalization) are grouped together.
    
    Args:
        issue: Dict with 'Member Name' and 'Parent Name' fields
    
    Returns:
        String (family key for grouping)
    
    Examples:
        {'Member Name': 'Net revenue  - Audit', ...} 
            → "Net revenue - Audit"
        
        {'Member Name': 'Net revenue - Audit', ...}
            → "Net revenue - Audit" (same key!)
        
        {'Member Name': '—', 'Parent Name': 'Orphan Parent - Audit'}
            → "(Orphan) Orphan Parent - Audit"
    """
    member_name = issue.get('Member Name', '')
    
    if member_name != '—':
        # Use cleaned member name
        cleaned = clean_name(member_name)
        return cleaned if cleaned else member_name
    else:
        # Orphan - use cleaned parent name with prefix
        parent_name = issue.get('Parent Name', '')
        cleaned_parent = clean_name(parent_name)
        if cleaned_parent:
            return f"(Orphan) {cleaned_parent}"
        else:
            return f"(Orphan) {parent_name}"


# ============================================================================
# LAYER 2: COLLECTION
# ============================================================================

def collect_all_issues(orphan_errors, orphan_warnings, mismatches,
                       duplicate_errors, duplicate_warnings, 
                       whitespace_grouped, vena_length_violations, df):
    """
    Collect all issues from validation functions into unified structure
    
    Converts each validation result type into standardized issue dict format.
    This is where we transform the various validation outputs into a common
    structure that can be grouped and numbered.
    
    Args:
        orphan_errors: Dict of orphan errors (parent doesn't exist)
        orphan_warnings: Dict of orphan warnings (may exist in Vena)
        mismatches: List of parent mismatch dicts
        duplicate_errors: List of duplicate error dicts
        duplicate_warnings: List of duplicate warning dicts
        whitespace_grouped: Dict of whitespace issues
        vena_length_violations: List of Vena length violation dicts
        df: Original DataFrame (for alias lookups)
    
    Returns:
        List of standardized issue dicts, each with:
        {
            'Type': 'Error' or 'Warning',
            'Category': 'Orphan', 'Parent Mismatch', 'Whitespace', etc.,
            'Member Name': str,
            'Parent Name': str,
            'Cause': str,
            'Rows': str (formatted row numbers)
        }
    """
    all_issues = []
    
    # ========================================================================
    # ORPHAN ERRORS - Parents with whitespace/Vena issues
    # ========================================================================
    # AUDITOR RECOMMENDATION: Add error handling to prevent crashes from
    # malformed validation outputs. Use "Log and Skip" strategy.
    # ========================================================================
    for parent_str, data in orphan_errors.items():
        try:
            excel_rows = [r + 2 for r in data['rows']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            if data.get('has_whitespace', False):
                # Two sub-issues will be created later by numbering logic
                # For now, create them as separate issues
                
                # Sub-issue 1: Orphan
                all_issues.append({
                    'Type': 'Error',
                    'Category': 'Orphan',
                    'Member Name': '—',
                    'Parent Name': parent_str,
                    'Cause': "Parent doesn't exist as member",
                    'Rows': rows_str
                })
                
                # Sub-issue 2: Whitespace
                ws_issues = []
                if '  ' in parent_str:
                    ws_issues.append('1 double space')
                if parent_str.startswith(' '):
                    ws_issues.append('leading space')
                if parent_str.endswith(' '):
                    ws_issues.append('trailing space')
                if '\t' in parent_str:
                    ws_issues.append('tab character')
                
                ws_cause = f"Parent name: {', '.join(ws_issues)}"
                
                all_issues.append({
                    'Type': 'Warning',
                    'Category': 'Whitespace',
                    'Member Name': '—',
                    'Parent Name': parent_str,
                    'Cause': ws_cause,
                    'Rows': rows_str
                })
            else:
                # Single orphan issue (no whitespace)
                all_issues.append({
                    'Type': 'Error',
                    'Category': 'Orphan',
                    'Member Name': '—',
                    'Parent Name': parent_str,
                    'Cause': "Parent doesn't exist as member",
                    'Rows': rows_str
                })
        except (KeyError, TypeError, AttributeError) as e:
            # Log malformed orphan error and skip
            print(f"WARNING: Skipping malformed orphan_error for '{parent_str}': {e}")
            continue
    
    # ========================================================================
    # PARENT MISMATCHES
    # ========================================================================
    for mismatch in mismatches:
        try:
            excel_row = mismatch['correct_member_row'] + 2
            
            # Format member name with alias if numeric
            member_name = mismatch["correct_member"]
            member_alias = mismatch["correct_member_alias"]
            if member_alias and str(member_alias) != 'nan':
                if any(char.isdigit() for char in member_name):
                    member_name = f"{member_name} ({member_alias})"
            
            parent_ref = mismatch["parent_ref"]
            cause = mismatch["cause_explanation"]
            
            child_rows = [child['row'] + 2 for child in mismatch['affected_children']]
            rows_str = ', '.join(map(str, sorted(child_rows)))
            
            all_issues.append({
                'Type': 'Error',
                'Category': 'Parent Mismatch',
                'Member Name': member_name,
                'Parent Name': parent_ref,
                'Cause': cause,
                'Rows': rows_str
            })
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            # Log malformed parent mismatch and skip
            print(f"WARNING: Skipping malformed parent_mismatch: {e}")
            continue
    
    # ========================================================================
    # DUPLICATE ERRORS
    # ========================================================================
    for dup in duplicate_errors:
        try:
            excel_rows = [inst['row'] + 2 for inst in dup['instances']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            # Format name with alias if numeric
            name = dup["member_name"]
            alias = dup['instances'][0]['alias'] if dup['instances'] else ''
            if alias and str(alias) != 'nan':
                if any(char.isdigit() for char in name):
                    name = f"{name} ({alias})"
            
            all_issues.append({
                'Type': 'Error',
                'Category': 'Duplicate',
                'Member Name': name,
                'Parent Name': '—',
                'Cause': f'{dup["total_children"]} children (fuzzy)',
                'Rows': rows_str
            })
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            # Log malformed duplicate error and skip
            print(f"WARNING: Skipping malformed duplicate_error: {e}")
            continue
    
    # ========================================================================
    # DUPLICATE WARNINGS
    # ========================================================================
    for dup in duplicate_warnings:
        try:
            excel_rows = [inst['row'] + 2 for inst in dup['instances']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            # Format name with alias if numeric
            name = dup["member_name"]
            alias = dup['instances'][0]['alias'] if dup['instances'] else ''
            if alias and str(alias) != 'nan':
                if any(char.isdigit() for char in name):
                    name = f"{name} ({alias})"
            
            all_issues.append({
                'Type': 'Warning',
                'Category': 'Duplicate Leaf',
                'Member Name': name,
                'Parent Name': '—',
                'Cause': 'All leaves (acceptable)',
                'Rows': rows_str
            })
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            # Log malformed duplicate warning and skip
            print(f"WARNING: Skipping malformed duplicate_warning: {e}")
            continue
    
    # ========================================================================
    # ORPHAN WARNINGS
    # ========================================================================
    for parent_str, data in orphan_warnings.items():
        try:
            excel_rows = [r + 2 for r in data['rows']]
            rows_str = ', '.join(map(str, sorted(excel_rows)))
            
            all_issues.append({
                'Type': 'Warning',
                'Category': 'External Parent',
                'Member Name': '—',
                'Parent Name': parent_str,
                'Cause': 'Parent not in file (may exist in Vena)',
                'Rows': rows_str
            })
        except (KeyError, TypeError, AttributeError) as e:
            # Log malformed orphan warning and skip
            print(f"WARNING: Skipping malformed orphan_warning for '{parent_str}': {e}")
            continue
    
    # ========================================================================
    # WHITESPACE ISSUES
    # ========================================================================
    for text, data in whitespace_grouped.items():
        try:
            member_rows = sorted(data['member_rows'])
            parent_rows = sorted(data['parent_rows'])
            
            # Format name with alias if numeric
            name = text
            alias = data['alias']
            if alias and str(alias) != 'nan':
                if any(char.isdigit() for char in text):
                    name = f"{text} ({alias})"
            
            # Determine if both columns or just one
            if member_rows and parent_rows:
                # Both columns have the issue
                all_rows = sorted(set(member_rows + parent_rows))
                excel_rows = [r + 2 for r in all_rows]
                rows_str = ', '.join(map(str, excel_rows))
                
                issue_text = ', '.join(data['issues'])
                cause = f"Both member and parent: {issue_text}"
                
                all_issues.append({
                    'Type': 'Warning',
                    'Category': 'Whitespace',
                    'Member Name': name,
                    'Parent Name': name,
                    'Cause': cause,
                    'Rows': rows_str
                })
            
            elif member_rows:
                # Only member column
                excel_rows = [r + 2 for r in member_rows]
                rows_str = ', '.join(map(str, excel_rows))
                
                issue_text = ', '.join(data['issues'])
                cause = f"Member name: {issue_text}"
                
                all_issues.append({
                    'Type': 'Warning',
                    'Category': 'Whitespace',
                    'Member Name': name,
                    'Parent Name': '—',
                    'Cause': cause,
                    'Rows': rows_str
                })
            
            elif parent_rows:
                # Only parent column
                excel_rows = [r + 2 for r in parent_rows]
                rows_str = ', '.join(map(str, excel_rows))
                
                issue_text = ', '.join(data['issues'])
                cause = f"Parent name: {issue_text}"
                
                all_issues.append({
                    'Type': 'Warning',
                    'Category': 'Whitespace',
                    'Member Name': '—',
                    'Parent Name': name,
                    'Cause': cause,
                    'Rows': rows_str
                })
        except (KeyError, TypeError, AttributeError, IndexError) as e:
            # Log malformed whitespace issue and skip
            print(f"WARNING: Skipping malformed whitespace_issue for '{text}': {e}")
            continue
    
    # ========================================================================
    # VENA LENGTH VIOLATIONS
    # ========================================================================
    for violation in vena_length_violations:
        try:
            row_num = violation['row']
            column = violation['column']
            name = violation['name']
            length = violation['length']
            
            all_issues.append({
                'Type': 'Error',
                'Category': 'Vena Restriction',
                'Member Name': name if column == 'Member' else '—',
                'Parent Name': name if column == 'Parent' else '—',
                'Cause': f'{column} exceeds 80 chars ({length} chars)',
                'Rows': str(row_num)
            })
        except (KeyError, TypeError, AttributeError) as e:
            # Log malformed vena violation and skip
            print(f"WARNING: Skipping malformed vena_length_violation: {e}")
            continue
    
    return all_issues


# ============================================================================
# LAYER 3: GROUPING
# ============================================================================

def group_issues_by_family(all_issues):
    """
    Group issues by cleaned member name
    
    This is where the magic happens! All issues for the same logical member
    (after whitespace normalization) are grouped together.
    
    Uses get_family_key() to determine the grouping key for each issue.
    
    Args:
        all_issues: List of standardized issue dicts
    
    Returns:
        Dict mapping family_key → list of issues
        
    Example:
        {
            "Net revenue - Audit": [
                issue1 (Parent Mismatch),
                issue2 (Parent Mismatch),
                issue3 (Parent Mismatch),
                issue4 (Whitespace),
                issue5 (Whitespace)
            ],
            "Costs and expenses - Audit": [
                issue1 (Parent Mismatch),
                issue2 (Whitespace)
            ]
        }
    """
    families = defaultdict(list)
    
    for issue in all_issues:
        family_key = get_family_key(issue)
        families[family_key].append(issue)
    
    return families


# ============================================================================
# LAYER 4: NUMBERING & OUTPUT
# ============================================================================

def assign_family_numbers(families):
    """
    Assign issue numbers to families
    
    Numbering Rules:
    - Single issue in family: #N
    - Multiple issues in family: #N.1, #N.2, #N.3, etc.
    
    Args:
        families: Dict mapping family_key → list of issues
    
    Returns:
        List of issues with 'Issue' field populated
        
    Example Input:
        {
            "Net revenue - Audit": [issue1, issue2, issue3, issue4, issue5]
        }
    
    Example Output:
        [
            {'Issue': '#5.1', ...},  # issue1
            {'Issue': '#5.2', ...},  # issue2
            {'Issue': '#5.3', ...},  # issue3
            {'Issue': '#5.4', ...},  # issue4
            {'Issue': '#5.5', ...}   # issue5
        ]
    """
    numbered_issues = []
    family_num = 1
    
    for family_key, issues in families.items():
        if len(issues) == 1:
            # Single issue - use #N format
            issues[0]['Issue'] = f"#{family_num}"
            numbered_issues.append(issues[0])
        else:
            # Multiple issues - use #N.1, #N.2, etc. format
            for sub_num, issue in enumerate(issues, start=1):
                issue['Issue'] = f"#{family_num}.{sub_num}"
                numbered_issues.append(issue)
        
        family_num += 1
    
    return numbered_issues


def build_master_table(numbered_issues):
    """
    Convert numbered issues into final table format
    
    Simply returns the issues list as-is, since they already have all
    required fields populated ('Issue', 'Type', 'Category', etc.)
    
    This function exists as a separate layer for:
    1. Future extensibility (add sorting, filtering, etc.)
    2. Clear separation of concerns (numbering vs formatting)
    3. Consistency with layered architecture
    
    Args:
        numbered_issues: List of issues with 'Issue' field populated
    
    Returns:
        List of dicts ready for pandas DataFrame
    """
    # For now, just return as-is
    # Future: Could add sorting, filtering, formatting here
    return numbered_issues
