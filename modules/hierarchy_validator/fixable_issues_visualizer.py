"""
Fixable Issues Visualizer - FIXED deduplication logic
Apple-style: Minimal, visual, intelligent
"""

import streamlit as st
import pandas as pd
from io import BytesIO


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


def highlight_differences(correct_text, problem_text):
    """
    Clean elegant highlighting - shows ONLY the problematic characters:
    - Extra spaces (2nd, 3rd... in consecutive spaces) → Red dot AFTER the correct space
    - Tabs, leading, trailing → Red markers (NO arrows, just dots)
    - Missing characters → Orange dot + annotation at end
    - Wrong characters → Orange background
    
    Example: "revenue  -" shows as "revenue ·-" (space, then red dot, then dash)
    """
    from rapidfuzz import distance
    
    result = []
    missing_chars = []
    
    # Get edit operations for typos/missing chars
    ops = distance.Levenshtein.editops(correct_text, problem_text)
    ops_list = [(op.tag, op.src_pos, op.dest_pos) for op in ops]
    
    # Build separate maps for whitespace vs character issues
    char_issues = {}  # dest_pos -> issue type (non-whitespace only)
    missing_chars = []  # (position, char) for missing non-whitespace
    missing_whitespace = []  # (position, char) for missing whitespace
    
    for op_type, src_pos, dest_pos in ops_list:
        if op_type == 'delete':
            # Missing character - check if it's whitespace or not
            missing_char = correct_text[src_pos]
            if missing_char in ' \t\n':
                # Missing whitespace - handle as RED
                missing_whitespace.append((dest_pos, missing_char))
            else:
                # Missing regular character - handle as ORANGE
                missing_chars.append((dest_pos, missing_char))
        elif op_type == 'replace':
            # Check if it's a character replacement (not whitespace)
            problem_char = problem_text[dest_pos] if dest_pos < len(problem_text) else ' '
            correct_char = correct_text[src_pos] if src_pos < len(correct_text) else ' '
            
            # Only mark as char issue if NEITHER is whitespace
            if problem_char not in ' \t\n' and correct_char not in ' \t\n':
                char_issues[dest_pos] = 'replace'
            # If either is whitespace, it will be caught by direct detection below
        elif op_type == 'insert':
            # Extra character - mark as char issue ONLY if it's NOT whitespace
            problem_char = problem_text[dest_pos] if dest_pos < len(problem_text) else ' '
            if problem_char not in ' \t\n':
                char_issues[dest_pos] = 'insert'
            # If it IS whitespace, we'll handle it in the direct detection below
    
    # Now walk through problem_text and detect patterns DIRECTLY
    i = 0
    missing_idx = 0
    missing_ws_idx = 0
    
    while i < len(problem_text):
        char = problem_text[i]
        
        # Insert missing WHITESPACE at the right position (RED)
        while missing_ws_idx < len(missing_whitespace) and missing_whitespace[missing_ws_idx][0] == i:
            missing_ws_char = missing_whitespace[missing_ws_idx][1]
            if missing_ws_char == '\t':
                result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">→TAB</span>')
            else:
                result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
            missing_ws_idx += 1
        
        # Insert missing CHARACTERS at the right position (ORANGE)
        while missing_idx < len(missing_chars) and missing_chars[missing_idx][0] == i:
            missing_char = missing_chars[missing_idx][1]
            result.append('<span style="background-color: #fff3e0; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
            missing_idx += 1
        
        # Check for whitespace issues - ALWAYS check these BEFORE char_issues
        if char == ' ':
            # Leading space - RED (not orange!)
            if i == 0:
                result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
                i += 1
            # Trailing space - RED, just dot (no arrow)
            elif i == len(problem_text) - 1:
                result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
                i += 1
            # Multiple consecutive spaces
            elif i + 1 < len(problem_text) and problem_text[i + 1] == ' ':
                # Count consecutive spaces
                space_count = 0
                j = i
                while j < len(problem_text) and problem_text[j] == ' ':
                    space_count += 1
                    j += 1
                
                # Show FIRST space as normal (it's correct - the first space bar hit)
                result.append(' ')
                
                # Show REMAINING spaces as red dots (they're extra - the 2nd, 3rd... space bar hits)
                for _ in range(space_count - 1):
                    result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
                
                i = j
            else:
                # Normal single space
                result.append(char)
                i += 1
        elif char == '\t':
            # Tab - RED
            result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">→TAB</span>')
            i += 1
        # Check for character issues (typos) - only if NOT already handled as whitespace
        elif i in char_issues:
            issue_type = char_issues[i]
            if issue_type in ['replace', 'insert']:
                result.append(f'<span style="background-color: #fff3e0; padding: 2px 4px; border-radius: 2px; font-weight: 600;">{char}</span>')
            i += 1
        else:
            # Normal character
            result.append(char)
            i += 1
    
    # Insert any remaining missing whitespace at the end (RED)
    while missing_ws_idx < len(missing_whitespace):
        missing_ws_char = missing_whitespace[missing_ws_idx][1]
        if missing_ws_char == '\t':
            result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">→TAB</span>')
        else:
            result.append('<span style="background-color: #ffebee; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
        missing_ws_idx += 1
    
    # Insert any remaining missing characters at the end (ORANGE)
    while missing_idx < len(missing_chars):
        missing_char = missing_chars[missing_idx][1]
        result.append('<span style="background-color: #fff3e0; padding: 2px 4px; border-radius: 2px; font-weight: 600;">·</span>')
        missing_idx += 1
    
    # Add missing character annotation at THE END (only for non-whitespace)
    if missing_chars:
        missing_str = ''.join([char for pos, char in missing_chars])
        result.append(f' <span style="color: #EA580C; font-size: 10px; font-weight: 600;">[missing: {missing_str}]</span>')
    
    return ''.join(result)


def create_fixable_issues_section(whitespace_issues, parent_mismatches, df):
    """
    CLEAN REBUILD - Proper deduplication and grouping
    
    Step 1: Collect all problem_text data (from both sources)
    Step 2: Deduplicate by problem_text (merge rows)
    Step 3: Group by normalized correct_text
    Step 4: Render
    """
    
    # Helper function for grouping key
    def get_grouping_key(text):
        """Fully normalized: lowercase + clean whitespace"""
        return text.strip().replace('\t', ' ').replace('  ', ' ').lower()
    
    # STEP 1: Collect ALL problem texts with their metadata
    # Key = problem_text, Value = {correct_text, rows, source}
    all_problems = {}
    
    # Collect from parent_mismatches
    if parent_mismatches:
        for mismatch in parent_mismatches:
            problem_text = mismatch['parent_ref']
            correct_text = mismatch['correct_member']
            
            if problem_text not in all_problems:
                all_problems[problem_text] = {
                    'correct_text': correct_text,
                    'rows': set(),
                    'has_typo': has_character_typo(correct_text, problem_text)
                }
            
            # Add rows
            for child in mismatch['affected_children']:
                all_problems[problem_text]['rows'].add(child['row'])
    
    # Collect from whitespace_issues
    if whitespace_issues:
        for ws in whitespace_issues:
            problem_text = ws.get('text', '')
            correct_text = problem_text.strip().replace('\t', ' ').replace('  ', ' ')
            
            if problem_text not in all_problems:
                all_problems[problem_text] = {
                    'correct_text': correct_text,
                    'rows': set(),
                    'has_typo': False
                }
            
            # Add rows (MERGE if already exists from parent_mismatches)
            for row in ws.get('rows', []):
                all_problems[problem_text]['rows'].add(row)
    
    # STEP 2: Group by normalized correct_text
    fix_groups = {}
    
    for problem_text, problem_data in all_problems.items():
        correct_text = problem_data['correct_text']
        grouping_key = get_grouping_key(correct_text)
        
        if grouping_key not in fix_groups:
            fix_groups[grouping_key] = {
                'correct_text': correct_text,
                'variations': [],  # List of unique problem texts
                'all_rows': set()
            }
        
        # Add this variation
        fix_groups[grouping_key]['variations'].append({
            'problem_text': problem_text,
            'rows': sorted(list(problem_data['rows'])),
            'has_typo': problem_data['has_typo']
        })
        
        # Add rows to total
        fix_groups[grouping_key]['all_rows'].update(problem_data['rows'])
    
    # STEP 3: Convert to list for rendering
    issues_list = []
    for fix_data in fix_groups.values():
        variations = fix_data['variations']
        
        # STEP 3.5: Smart row assignment - each row goes to its MOST SPECIFIC variation
        # Build a map: row -> best variation for that row
        row_to_variation = {}
        
        for var_idx, variation in enumerate(variations):
            problem_text = variation['problem_text']
            
            # Count how many issues this variation has
            issue_count = 0
            # Check for typos (missing chars, wrong chars)
            if variation.get('has_typo', False):
                issue_count += 1
            # Check for whitespace issues
            if '  ' in problem_text or problem_text.startswith(' ') or problem_text.endswith(' ') or '\t' in problem_text:
                issue_count += 1
            
            # Assign each row to this variation if it's more specific
            for row in variation['rows']:
                if row not in row_to_variation:
                    row_to_variation[row] = {'var_idx': var_idx, 'issue_count': issue_count}
                elif issue_count > row_to_variation[row]['issue_count']:
                    # This variation has MORE issues, so it's more specific - take the row
                    row_to_variation[row] = {'var_idx': var_idx, 'issue_count': issue_count}
        
        # Now rebuild variations with only their assigned rows
        for var_idx, variation in enumerate(variations):
            assigned_rows = [row for row, assignment in row_to_variation.items() 
                           if assignment['var_idx'] == var_idx]
            variation['rows'] = sorted(assigned_rows)
        
        # Sort variations by first row number (after reassignment)
        variations = sorted(variations, key=lambda x: x['rows'][0] if x['rows'] else float('inf'))
        
        issues_list.append({
            'correct_text': fix_data['correct_text'],
            'variations': variations,
            'all_rows': sorted(list(fix_data['all_rows'])),
            'variation_count': len(variations)
        })
    
    # Sort by first row number
    issues_list.sort(key=lambda x: x['all_rows'][0] if x['all_rows'] else 0)
    
    total_fixable = len(issues_list)
    
    if total_fixable == 0:
        return
    
    # Section header
    st.markdown("---")
    st.markdown("### Fixable Issues")
    
    # Simple count
    st.markdown(f"<p style='color: #666; margin-bottom: 20px;'>{total_fixable} issue{'s' if total_fixable != 1 else ''} found</p>", unsafe_allow_html=True)
    
    # Expandable details
    with st.expander("Show details", expanded=False):
        
        # Show each fix group
        for issue in issues_list:
            correct_text = issue['correct_text']
            variations = issue['variations']
            all_rows = ', '.join(map(str, [r + 2 for r in issue['all_rows']]))
            variation_count = issue['variation_count']
            
            # Determine border color based on whether ANY variation has a typo
            has_any_typo = any(v['has_typo'] for v in variations)
            border_color = "#EA580C" if has_any_typo else "#DC2626"
            
            # Build variation display
            if variation_count == 1:
                # Single variation - show it normally
                var = variations[0]
                visual = highlight_differences(correct_text, var['problem_text'])
                
                st.markdown(f"""
                <div style="margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 3px solid {border_color};">
                    <div style="font-family: monospace; font-size: 14px; margin-bottom: 8px;">
                        {visual}
                    </div>
                    <div style="font-size: 11px; color: #999; margin-bottom: 8px;">
                        Rows: {all_rows}
                    </div>
                    <div style="font-size: 12px; color: #999; margin-bottom: 8px;">↓</div>
                    <div style="font-family: monospace; font-size: 14px; color: #16a34a;">
                        {correct_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Multiple variations - show all of them
                # Build each variation separately to avoid nested f-string issues
                st.markdown(f"""
                <div style="margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 3px solid {border_color};">
                    <div style="font-size: 12px; color: #666; margin-bottom: 10px; font-weight: 500;">
                        {variation_count} variations → same fix:
                    </div>
                """, unsafe_allow_html=True)
                
                # Render each variation
                for var in variations:
                    var_rows = ', '.join(map(str, [r + 2 for r in var['rows']]))
                    visual = highlight_differences(correct_text, var['problem_text'])
                    
                    st.markdown(f"""
                    <div style="margin-bottom: 10px; padding: 8px; background: #fff; border-radius: 4px;">
                        <div style="font-family: monospace; font-size: 13px; margin-bottom: 4px;">
                            {visual}
                        </div>
                        <div style="font-size: 11px; color: #999;">
                            Rows: {var_rows}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show the fix result - NO row repetition
                st.markdown(f"""
                    <div style="font-size: 12px; color: #999; margin: 12px 0 8px 0;">↓</div>
                    <div style="font-family: monospace; font-size: 14px; color: #16a34a; font-weight: 500;">
                        {correct_text}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Download button
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Apply fixes
    fixed_df = df.copy()
    
    # Fix all variations → correct text for each group
    for issue in issues_list:
        correct_text = issue['correct_text']
        
        for variation in issue['variations']:
            problem_text = variation['problem_text']
            
            # Replace in both columns
            fixed_df['_member_name'] = fixed_df['_member_name'].replace(problem_text, correct_text)
            fixed_df['_parent_name'] = fixed_df['_parent_name'].replace(problem_text, correct_text)
    
    # Download
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
