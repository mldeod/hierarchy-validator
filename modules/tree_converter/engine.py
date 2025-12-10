#!/usr/bin/env python3
"""
Excel Tree to Parent-Child Converter
Converts visual Excel hierarchies to structured parent-child tables
"""

import pandas as pd
from treelib import Tree, Node
from collections import defaultdict
import re

class TreeParser:
    """Parse Excel tree format and convert to parent-child table"""
    
    def __init__(self):
        self.tree = Tree()
        self.errors = []
        self.warnings = []
        self.member_count = 0
        self.empty_rows_skipped = 0
        self.all_member_rows = []  # Track ALL members including duplicates for output
        
    def parse_excel_tree(self, file_path, max_levels=10, alias_column=10, operator_column=11):
        """
        Parse Excel tree format
        
        Args:
            file_path: Path to Excel file
            max_levels: Number of columns to check for hierarchy (default 10)
            alias_column: Column index for aliases (default 10 = column K, 0-indexed)
            operator_column: Column index for operators (default 11 = column L, 0-indexed)
        
        Returns:
            tuple: (tree, errors, warnings, stats)
        """
        print("🌳 Reading Excel file...")
        
        try:
            # Read Excel without headers
            df = pd.read_excel(file_path, header=None)
        except Exception as e:
            self.errors.append({
                'row': 0,
                'type': 'File Error',
                'member': '',
                'message': f'Could not read Excel file: {str(e)}'
            })
            return self.tree, self.errors, self.warnings, self._get_stats()
        
        print(f"📊 Found {len(df)} rows")
        
        # Skip header row if it exists
        start_row = 0
        if df.iloc[0, 0] and str(df.iloc[0, 0]).lower().startswith('level'):
            start_row = 1
            print(f"⏭️  Skipping header row")
        
        # Track parents at each level
        parent_stack = {}  # {level: node_id}
        
        # Track all members by name to detect first occurrence
        member_nodes = {}  # {member_name: node_id} - only first occurrence
        
        # Track all occurrences for duplicate warnings
        all_occurrences = defaultdict(list)  # {name: [row_numbers]}
        
        # Process each row
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            excel_row = idx + 1  # Excel row number (1-indexed, idx already accounts for header skip)
            
            # Find first non-empty cell (determines level)
            level = None
            member_name = None
            member_name_raw = None
            
            for col_idx in range(max_levels):
                cell_value = row[col_idx]
                if pd.notna(cell_value) and str(cell_value).strip():
                    level = col_idx
                    member_name_raw = str(cell_value)
                    member_name = member_name_raw.strip()
                    
                    # Check for whitespace issues
                    if member_name_raw != member_name:
                        self.warnings.append({
                            'type': 'Whitespace Trimmed',
                            'member': member_name,
                            'rows': [excel_row],
                            'message': f"Auto-trimmed leading/trailing whitespace"
                        })
                    break
            
            # Skip completely empty rows
            if level is None:
                self.empty_rows_skipped += 1
                continue
            
            # Get alias from specified column
            alias = None
            if alias_column < len(row):
                alias_value = row[alias_column]
                if pd.notna(alias_value):
                    alias = str(alias_value).strip()
            
            # Get operator from specified column (default to '+')
            operator = '+'
            if operator_column < len(row):
                operator_value = row[operator_column]
                if pd.notna(operator_value):
                    op = str(operator_value).strip()
                    # Validate operator
                    if op in ['+', '-', '~']:
                        operator = op
                    else:
                        self.warnings.append({
                            'type': 'Invalid Operator',
                            'member': member_name,
                            'rows': [excel_row],
                            'message': f"Invalid operator '{op}' (must be +, -, or ~). Defaulting to '+'"
                        })
            
            # Track all occurrences
            all_occurrences[member_name].append(excel_row)
            
            # Determine parent name for this row
            parent_name_for_row = None
            if level > 0:
                if level - 1 in parent_stack:
                    parent_node = self.tree.get_node(parent_stack[level - 1])
                    parent_name_for_row = parent_node.tag
            
            # If this member already exists, use it for navigation (don't create new node)
            if member_name in member_nodes:
                # This is a repeated name - track for output but use existing node for context
                self.all_member_rows.append({
                    'member_name': member_name,
                    'alias': alias,
                    'parent_name': parent_name_for_row,
                    'operator': operator,
                    'level': level,
                    'row': excel_row
                })
                
                existing_node_id = member_nodes[member_name]
                parent_stack[level] = existing_node_id
                
                # Clear deeper levels
                levels_to_remove = [l for l in parent_stack.keys() if l > level]
                for l in levels_to_remove:
                    del parent_stack[l]
                
                continue  # Don't create a new node
            
            # Validate: Check if level jumped more than 1
            if parent_stack:
                max_existing_level = max(parent_stack.keys())
                if level > max_existing_level + 1:
                    self.errors.append({
                        'type': 'Skipped Level',
                        'row': excel_row,
                        'member': member_name,
                        'message': f"Cannot skip hierarchy levels. '{member_name}' is at level {level}, but there's no parent at level {max_existing_level + 1}. Add a level {max_existing_level + 1} parent, then resubmit."
                    })
                    continue
            
            # Determine parent
            parent_id = None
            parent_name = None
            if level > 0:
                # Look for parent at level - 1
                if level - 1 in parent_stack:
                    parent_id = parent_stack[level - 1]
                    parent_node = self.tree.get_node(parent_id)
                    parent_name = parent_node.tag
                else:
                    self.errors.append({
                        'type': 'Missing Parent',
                        'row': excel_row,
                        'member': member_name,
                        'message': f"'{member_name}' at level {level} has no parent at level {level - 1}. Add a parent member at level {level - 1}, then resubmit."
                    })
                    continue
            else:
                # This is a root node (level 0) - clear parent stack for clean slate
                parent_stack = {}
            
            # Create unique node ID
            node_id = f"node_{self.member_count}"
            
            # Create node in tree
            try:
                self.tree.create_node(
                    tag=member_name,
                    identifier=node_id,
                    parent=parent_id,
                    data={
                        'alias': alias,
                        'operator': operator,
                        'level': level,
                        'row': excel_row
                    }
                )
                
                # Track this member
                member_nodes[member_name] = node_id
                
                # Track for output
                self.all_member_rows.append({
                    'member_name': member_name,
                    'alias': alias,
                    'parent_name': parent_name,
                    'operator': operator,
                    'level': level,
                    'row': excel_row
                })
                
                # Update parent stack
                parent_stack[level] = node_id
                
                # Clear deeper levels (we're back at this level)
                levels_to_remove = [l for l in parent_stack.keys() if l > level]
                for l in levels_to_remove:
                    del parent_stack[l]
                
                self.member_count += 1
                
            except Exception as e:
                error_msg = str(e)
                # Check if this is a "multiple roots" error
                if "one root" in error_msg.lower():
                    # Get the first root name for better error message
                    first_root = None
                    for node_id in member_nodes.values():
                        node = self.tree.get_node(node_id)
                        if node.data['level'] == 0:
                            first_root = node.tag
                            break
                    
                    if first_root:
                        self.errors.append({
                            'type': 'Multiple Root Nodes',
                            'row': excel_row,
                            'member': member_name,
                            'message': f"File contains multiple root nodes ('{first_root}' and '{member_name}'). Please split into separate files - one for each root - and submit individually."
                        })
                    else:
                        self.errors.append({
                            'type': 'Multiple Root Nodes',
                            'row': excel_row,
                            'member': member_name,
                            'message': f"Multiple root nodes detected. Please split into separate files - one for each root - and submit individually."
                        })
                    # Stop processing - subsequent rows will fail due to missing parent
                    print(f"⚠️  Stopped processing after multiple root error at row {excel_row}")
                    break
                else:
                    self.errors.append({
                        'type': 'Tree Error',
                        'row': excel_row,
                        'member': member_name,
                        'message': f"Unable to add '{member_name}' to hierarchy: {error_msg}. Please check the structure and resubmit."
                    })
        
        # Check for duplicates (members that appeared more than once)
        for member_name, rows in all_occurrences.items():
            if len(rows) > 1:
                self.warnings.append({
                    'type': 'Repeated Member',
                    'member': member_name,
                    'rows': rows,
                    'message': f"Member '{member_name}' appears {len(rows)} times (used for navigation)"
                })
        
        # Add warning for empty rows if any were skipped
        if self.empty_rows_skipped > 0:
            self.warnings.append({
                'type': 'Empty Rows Skipped',
                'member': 'N/A',
                'rows': [],
                'message': f"Skipped {self.empty_rows_skipped} empty row{'s' if self.empty_rows_skipped > 1 else ''}"
            })
        
        # Generate stats
        stats = {
            'total_members': self.member_count,
            'max_depth': self.tree.depth() if self.member_count > 0 else 0,
            'leaf_count': len(self.tree.leaves()) if self.member_count > 0 else 0,
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }
        
        print(f"✅ Parsed {self.member_count} members")
        print(f"📏 Max depth: {stats['max_depth']}")
        print(f"🍃 Leaf nodes: {stats['leaf_count']}")
        
        if self.errors:
            print(f"❌ {len(self.errors)} errors found")
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} warnings found")
        
        return self.tree, self.errors, self.warnings, stats
    
    def tree_to_parent_child(self, dimension_name="Account", operator="+", cmd="+"):
        """
        Convert tree to Vena hierarchy format (6 columns)
        
        Args:
            dimension_name: Vena dimension name (e.g., "Account", "Cost Center")
            operator: Default operator for rollup (+, -, ~)
            cmd: Default command (+ for add, - for delete)
        
        Returns:
            pandas.DataFrame with Vena columns:
            _dim, _member_name, _member_alias, _parent_name, _operator, _cmd
        """
        if self.member_count == 0:
            return pd.DataFrame(columns=[
                '_dim', '_member_name', '_member_alias', 
                '_parent_name', '_operator', '_cmd'
            ])
        
        rows = []
        
        # Use all_member_rows which includes duplicates
        for member_data in self.all_member_rows:
            rows.append({
                '_dim': dimension_name,
                '_member_name': member_data['member_name'],
                '_member_alias': member_data['alias'] if member_data['alias'] else '',
                '_parent_name': member_data['parent_name'] if member_data['parent_name'] else '',
                '_operator': member_data['operator'],
                '_cmd': cmd
            })
        
        df = pd.DataFrame(rows)
        
        print(f"📋 Created Vena hierarchy table: {len(df)} rows x 6 columns")
        print(f"   Dimension: {dimension_name} | Operator: {operator} | Cmd: {cmd}")
        
        return df
    
    def visualize_hierarchy_with_duplicates(self):
        """
        Create text tree visualization that shows ALL members including duplicates
        """
        if not self.all_member_rows:
            return "No members to display"
        
        # Build tree structure from all_member_rows
        lines = []
        
        # Group by level for organized display
        by_level = {}
        for member_data in self.all_member_rows:
            level = member_data['level']
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(member_data)
        
        # Track which members appear multiple times
        member_counts = {}
        for member_data in self.all_member_rows:
            name = member_data['member_name']
            member_counts[name] = member_counts.get(name, 0) + 1
        
        # Build tree recursively
        def add_children(parent_name, level, prefix=""):
            children = [m for m in by_level.get(level + 1, []) if m['parent_name'] == parent_name]
            
            for i, child in enumerate(children):
                is_last = (i == len(children) - 1)
                connector = "└── " if is_last else "├── "
                
                # Mark duplicates
                name = child['member_name']
                if member_counts[name] > 1:
                    display_name = f"{name} (shared)"
                else:
                    display_name = name
                
                lines.append(f"{prefix}{connector}{display_name}")
                
                # Recurse for children
                if is_last:
                    add_children(name, level + 1, prefix + "    ")
                else:
                    add_children(name, level + 1, prefix + "│   ")
        
        # Start with root(s)
        roots = by_level.get(0, [])
        for root in roots:
            lines.append(root['member_name'])
            add_children(root['member_name'], 0, "")
            if len(roots) > 1:
                lines.append("")  # Blank line between multiple roots
        
        return "\n".join(lines)
    
    def get_tree_visualization(self):
        """Get ASCII tree visualization"""
        if self.member_count == 0:
            return "Empty tree"
        return self.tree.show(stdout=False)


# Test function
def test_parser():
    """Test the parser with sample file"""
    print("=" * 80)
    print("🧪 TESTING TREE PARSER")
    print("=" * 80)
    
    parser = TreeParser()
    
    # Parse the sample file
    tree, errors, warnings, stats = parser.parse_excel_tree('sample_hierarchy_tree.xlsx')
    
    print("\n" + "=" * 80)
    print("📊 STATISTICS")
    print("=" * 80)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    if errors:
        print("\n" + "=" * 80)
        print("❌ ERRORS")
        print("=" * 80)
        for err in errors:
            print(f"   Row {err['row']}: {err['message']}")
    
    if warnings:
        print("\n" + "=" * 80)
        print("⚠️  WARNINGS")
        print("=" * 80)
        for warn in warnings:
            print(f"   {warn['message']} (rows: {', '.join(map(str, warn['rows']))})")
    
    # Show tree visualization
    print("\n" + "=" * 80)
    print("🌲 TREE VISUALIZATION (first 30 lines)")
    print("=" * 80)
    tree_vis = parser.get_tree_visualization()
    lines = tree_vis.split('\n')[:30]
    print('\n'.join(lines))
    if len(tree_vis.split('\n')) > 30:
        print(f"   ... and {len(tree_vis.split('\n')) - 30} more lines")
    
    # Convert to parent-child
    print("\n" + "=" * 80)
    print("📋 VENA HIERARCHY TABLE (first 10 rows)")
    print("=" * 80)
    df = parser.tree_to_parent_child(dimension_name="Account", operator="+", cmd="+")
    print(df.head(10).to_string(index=False))
    print(f"\n   ... and {len(df) - 10} more rows")
    
    # Save output
    output_file = 'sample_hierarchy_vena_format.xlsx'
    df.to_excel(output_file, index=False)
    print(f"\n✅ Saved to: {output_file}")
    
    print("\n" + "=" * 80)
    print("🎉 TEST COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    test_parser()
