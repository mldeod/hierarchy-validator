"""
Hierarchy Validator - Validation Engine
Core validation functions for parent-child hierarchies
"""

import pandas as pd
from collections import defaultdict
from rapidfuzz import fuzz, distance

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
