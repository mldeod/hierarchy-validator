"""
Hierarchy Validator - Validation Engine
Core validation functions for parent-child hierarchies
Extracted from vena_hierarchy_validator_v8_final.py
"""

import pandas as pd
from collections import defaultdict
from rapidfuzz import fuzz, distance


def get_member_display(member, alias):
    """Format member display with alias"""
    if alias and str(alias) != 'nan':
        return f"{member} ({alias})"
    return member


def classify_difference(member_name, parent_ref):
    """
    Classify the type of difference between member name (reference) and parent reference (analyzed)
    Returns: (category, explanation, is_whitespace_only, is_vena_invalid)
    
    is_vena_invalid = True if the difference involves leading/trailing whitespace or tabs
    """
    from rapidfuzz.distance import Levenshtein
    
    # Get edit operations
    ops = Levenshtein.editops(member_name, parent_ref)
    
    if not ops:
        return "identical", "", False, False
    
    # Check if ALL operations are whitespace
    whitespace_only = True
    for op_type, src_pos, dest_pos in ops:
        if op_type == 'delete':
            char = member_name[src_pos] if src_pos < len(member_name) else ' '
        elif op_type == 'insert':
            char = parent_ref[dest_pos] if dest_pos < len(parent_ref) else ' '
        elif op_type == 'replace':
            char1 = member_name[src_pos] if src_pos < len(member_name) else ' '
            char2 = parent_ref[dest_pos] if dest_pos < len(parent_ref) else ' '
            if char1 not in ' \t\n' and char2 not in ' \t\n':
                whitespace_only = False
                break
        
        if char not in ' \t\n':
            whitespace_only = False
            break
    
    # If whitespace-only, explain the whitespace issue
    if whitespace_only:
        return explain_whitespace_difference(member_name, parent_ref, ops)
    
    # Check if only capitalization difference
    if member_name.lower() == parent_ref.lower():
        # Find which character differs
        for i, (c1, c2) in enumerate(zip(member_name, parent_ref)):
            if c1 != c2:
                return "capitalization", f"'{c1}' vs '{c2}' at position {i}", False, False
        return "capitalization", "Case difference", False, False
    
    # Explain the typo
    if len(ops) == 1:
        op_type, src_pos, dest_pos = ops[0]
        
        if op_type == 'delete':
            # Delete from member to get to parent = parent is MISSING this char
            char = member_name[src_pos]
            return "typo", f"Missing '{char}' in parent at pos {src_pos}", False, False
        elif op_type == 'insert':
            # Insert into member to get to parent = parent has EXTRA char
            char = parent_ref[dest_pos]
            return "typo", f"Extra '{char}' in parent at pos {dest_pos}", False, False
        elif op_type == 'replace':
            char1 = member_name[src_pos]
            char2 = parent_ref[dest_pos]
            return "typo", f"'{char2}' Should be '{char1}' at pos {src_pos}", False, False
    
    # Multiple operations
    return "typo", f"{len(ops)} Character differences", False, False


def explain_whitespace_difference(str1, str2, ops):
    """Explain whitespace-specific differences
    
    Returns: (category, explanation, is_whitespace_only, is_vena_invalid)
    is_vena_invalid = True if involves leading/trailing whitespace or tabs (INVALID in Vena)
    """
    issues = []
    is_vena_invalid = False
    
    # Check for Vena-invalid whitespace: leading, trailing, or tabs
    has_leading = str1.lstrip() != str1 or str2.lstrip() != str2
    has_trailing = str1.rstrip() != str1 or str2.rstrip() != str2
    has_tabs = '\t' in str1 or '\t' in str2
    
    if has_leading or has_trailing or has_tabs:
        is_vena_invalid = True
    
    # Analyze each operation to see what's different
    for op_type, src_pos, dest_pos in ops:
        if op_type == 'insert':
            # Parent has extra character
            char = str2[dest_pos] if dest_pos < len(str2) else ' '
            if char == ' ':
                # Check if it's trailing
                if dest_pos == len(str2) - 1:
                    issues.append("trailing space")
                # Check if it creates double space
                elif dest_pos > 0 and str2[dest_pos - 1] == ' ':
                    issues.append("extra space")
                elif dest_pos < len(str2) - 1 and str2[dest_pos + 1] == ' ':
                    issues.append("extra space")
                else:
                    issues.append("extra space")
            elif char == '\t':
                issues.append("tab character")
        elif op_type == 'delete':
            # Member has extra character (parent missing it)
            char = str1[src_pos] if src_pos < len(str1) else ' '
            if char == ' ':
                issues.append("missing space")
            elif char == '\t':
                issues.append("missing tab")
    
    if not issues:
        # Fallback - check for general whitespace issues
        if '  ' in str1 or '  ' in str2:
            issues.append("double space")
        if has_trailing:
            issues.append("trailing space")
        if has_leading:
            issues.append("leading space")
        if has_tabs:
            issues.append("tab character")
    
    explanation = ", ".join(set(issues))  # Remove duplicates
    
    # Add Vena warning to explanation if invalid (lowercase for now)
    if is_vena_invalid:
        explanation = f"{explanation} (invalid in vena)"
    
    # Fix "Vena" capitalization (the exception!)
    explanation = explanation.replace("vena", "Vena")
    
    # Capitalize only first letter of the whole explanation
    if explanation:
        explanation = explanation[0].upper() + explanation[1:] if len(explanation) > 1 else explanation.upper()
    
    return "whitespace", explanation, True, is_vena_invalid


def count_children_fuzzy(df, member_name, max_edit_distance=2):
    """Count children using fuzzy matching"""
    total_children = 0
    for idx, row in df.iterrows():
        parent_ref = row['_parent_name']
        if pd.notna(parent_ref):
            parent_str = str(parent_ref)
            if parent_str == member_name:
                total_children += 1
            else:
                edit_dist = distance.Levenshtein.distance(member_name, parent_str)
                if 1 <= edit_dist <= max_edit_distance:
                    total_children += 1
    return total_children


def find_orphans(df, max_edit_distance=2):
    """
    Find TRUE ORPHANS - parent references that don't exist as members at all
    (not even with fuzzy matching)
    """
    # Get all member names
    member_names = set()
    for idx, row in df.iterrows():
        member = str(row['_member_name'])
        member_names.add(member)
    
    # Find orphans
    orphans = defaultdict(lambda: {'rows': [], 'has_whitespace': False, 'is_vena_invalid': False})
    
    for idx, row in df.iterrows():
        parent_ref = row['_parent_name']
        if pd.notna(parent_ref):
            parent_str = str(parent_ref)
            
            # Check if parent exists (exact match)
            if parent_str in member_names:
                continue
            
            # Check if parent exists (fuzzy match)
            has_fuzzy_match = False
            for member in member_names:
                edit_dist = distance.Levenshtein.distance(parent_str, member)
                if 1 <= edit_dist <= max_edit_distance:
                    has_fuzzy_match = True
                    break
            
            if not has_fuzzy_match:
                # TRUE ORPHAN - no member exists at all!
                orphans[parent_str]['rows'].append(idx)
                
                # Check if orphan has whitespace issues
                # Vena-invalid: leading/trailing/tabs
                has_leading = parent_str.lstrip() != parent_str
                has_trailing = parent_str.rstrip() != parent_str
                has_tabs = '\t' in parent_str
                has_double_spaces = '  ' in parent_str
                
                if has_leading or has_trailing or has_tabs:
                    orphans[parent_str]['has_whitespace'] = True
                    orphans[parent_str]['is_vena_invalid'] = True
                elif has_double_spaces:
                    orphans[parent_str]['has_whitespace'] = True
                    orphans[parent_str]['is_vena_invalid'] = False
    
    return orphans


def find_parent_mismatches(df, max_edit_distance=2):
    """Find parent name mismatches using fuzzy matching with cause classification"""
    member_names = {}
    for idx, row in df.iterrows():
        member = str(row['_member_name'])
        member_alias = row.get('_member_alias', '') if '_member_alias' in df.columns else ''
        member_names[member] = {
            'row': idx,
            'alias': member_alias if pd.notna(member_alias) else ''
        }
    
    mismatches = []
    processed_parents = set()
    
    for idx, row in df.iterrows():
        parent_ref = row['_parent_name']
        if pd.notna(parent_ref):
            parent_str = str(parent_ref)
            
            if parent_str in processed_parents:
                continue
            
            if parent_str not in member_names:
                best_match = None
                min_distance = float('inf')
                
                for member in member_names.keys():
                    edit_dist = distance.Levenshtein.distance(parent_str, member)
                    if 1 <= edit_dist <= max_edit_distance and edit_dist < min_distance:
                        min_distance = edit_dist
                        best_match = member
                
                if best_match:
                    # Classify the difference
                    category, explanation, is_whitespace, is_vena_invalid = classify_difference(best_match, parent_str)
                    
                    children = []
                    for child_idx, child_row in df.iterrows():
                        child_parent = str(child_row['_parent_name']) if pd.notna(child_row['_parent_name']) else None
                        if child_parent:
                            child_edit_dist = distance.Levenshtein.distance(best_match, child_parent)
                            if 1 <= child_edit_dist <= max_edit_distance:
                                similarity = fuzz.ratio(best_match, child_parent)
                                children.append({
                                    'row': child_idx,
                                    'member': str(child_row['_member_name']),
                                    'alias': child_row.get('_member_alias', '') if '_member_alias' in df.columns else '',
                                    'parent_name': child_parent,
                                    'edit_distance': child_edit_dist,
                                    'similarity': similarity
                                })
                    
                    if children:
                        mismatches.append({
                            'correct_member': best_match,
                            'correct_member_alias': member_names[best_match]['alias'],
                            'correct_member_row': member_names[best_match]['row'],
                            'parent_ref': parent_str,
                            'cause_category': category,
                            'cause_explanation': explanation,
                            'is_whitespace': is_whitespace,
                            'is_vena_invalid': is_vena_invalid,
                            'affected_children': children
                        })
                        processed_parents.add(parent_str)
    
    return mismatches


def find_duplicate_members(df):
    """Find duplicate member names with fuzzy children counting"""
    member_instances = defaultdict(list)
    
    for idx, row in df.iterrows():
        member = str(row['_member_name'])
        member_alias = row.get('_member_alias', '') if '_member_alias' in df.columns else ''
        member_instances[member].append({
            'row': idx,
            'alias': member_alias if pd.notna(member_alias) else ''
        })
    
    duplicate_errors = []
    duplicate_warnings = []
    
    for member_name, instances in member_instances.items():
        if len(instances) >= 2:
            total_children = count_children_fuzzy(df, member_name, max_edit_distance=2)
            
            if total_children > 0:
                duplicate_errors.append({
                    'member_name': member_name,
                    'instances': instances,
                    'total_children': total_children
                })
            else:
                duplicate_warnings.append({
                    'member_name': member_name,
                    'instances': instances
                })
    
    return duplicate_errors, duplicate_warnings


def find_whitespace_issues(df):
    """Find internal whitespace issues (double spaces) grouped by distinct text
    
    Note: Leading/trailing whitespace and tabs are handled by Vena Restrictions
    """
    grouped_issues = defaultdict(lambda: {'rows': [], 'alias_example': '', 'issues': []})
    
    for idx, row in df.iterrows():
        member = str(row['_member_name'])
        parent = str(row['_parent_name']) if pd.notna(row['_parent_name']) else None
        member_alias = row.get('_member_alias', '') if '_member_alias' in df.columns else ''
        
        # Check member name - ONLY internal whitespace issues
        # (leading/trailing/tabs now handled by Vena Restrictions)
        member_issues = []
        if '  ' in member:
            member_issues.append(f"{member.count('  ')} double space")
        
        if member_issues:
            key = ('_member_name', member)
            grouped_issues[key]['rows'].append(idx)
            grouped_issues[key]['alias_example'] = member_alias if pd.notna(member_alias) else ''
            grouped_issues[key]['issues'] = member_issues
        
        # Check parent name - ONLY internal whitespace issues
        # (leading/trailing/tabs now handled by Vena Restrictions)
        if parent:
            parent_issues = []
            if '  ' in parent:
                parent_issues.append(f"{parent.count('  ')} double space")
            
            if parent_issues:
                key = ('_parent_name', parent)
                grouped_issues[key]['rows'].append(idx)
                grouped_issues[key]['alias_example'] = member_alias if pd.notna(member_alias) else ''
                grouped_issues[key]['issues'] = parent_issues
    
    whitespace_issues = []
    for (column, text), data in grouped_issues.items():
        whitespace_issues.append({
            'column': column,
            'text': text,
            'highlighted': text,  # No middle dots - just use original text
            'rows': sorted(data['rows']),
            'alias_example': data['alias_example'],
            'issues': data['issues']
        })
    
    whitespace_issues.sort(key=lambda x: x['rows'][0])
    return whitespace_issues
