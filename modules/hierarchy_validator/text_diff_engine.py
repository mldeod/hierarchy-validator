"""
Text Difference Engine - Modular Architecture
==============================================

The Mille-Feuille: Four Beautiful Layers
-----------------------------------------
Layer 1: StringCleaner    - Whitespace normalization
Layer 2: DiffEngine       - Semantic edit detection with look-ahead
Layer 3: Annotator        - Business rules for annotations
Layer 4: HtmlRenderer     - Gorgeous Scandinavian presentation

Author: Manu + Claude + The Auditor
Date: January 2, 2026
Version: 3.0.0 - Pipeline Pattern Refactor
"""

from dataclasses import dataclass
from typing import List, Tuple, Set, Optional
from enum import Enum


# ============================================================================
# DATA STRUCTURES - The Building Blocks
# ============================================================================

class EditType(Enum):
    """Semantic edit types - what ACTUALLY happened"""
    TRANSPOSITION = "transposition"  # Two adjacent chars swapped
    TYPO = "typo"                    # Wrong character
    DELETION = "deletion"            # Character missing
    INSERTION = "insertion"          # Extra character
    WHITESPACE = "whitespace"        # Whitespace issue


@dataclass
class SemanticEdit:
    """
    A semantic understanding of what changed
    
    This is what the DiffEngine returns - human-meaningful edits
    instead of raw Levenshtein operations.
    """
    edit_type: EditType
    position: int                    # Position in problem text
    correct_char: str               # What it should be
    problem_char: str               # What it actually is
    pair_position: Optional[int] = None  # For transpositions: the other char's position
    
    def __repr__(self):
        if self.edit_type == EditType.TRANSPOSITION:
            return f"TRANSPOSITION({self.correct_char}{self.problem_char} at {self.position},{self.pair_position})"
        elif self.edit_type == EditType.DELETION:
            return f"DELETION({self.correct_char} missing at {self.position})"
        else:
            return f"{self.edit_type.value.upper()}({self.correct_char}→{self.problem_char} at {self.position})"


@dataclass
class WhitespaceMap:
    """
    Tracks whitespace issues separately from character issues
    
    This keeps whitespace analysis clean and isolated.
    """
    leading_spaces: List[int]        # Positions of leading spaces
    trailing_spaces: List[int]       # Positions of trailing spaces
    double_spaces: List[Tuple[int, int]]  # (start, end) of double space runs
    tabs: List[int]                  # Tab character positions
    
    def has_issues(self) -> bool:
        """Does this text have any whitespace problems?"""
        return bool(self.leading_spaces or self.trailing_spaces or 
                   self.double_spaces or self.tabs)


@dataclass
class CleanString:
    """
    A normalized string with position mapping back to original
    
    Example:
    Original: "hello  world" (double space)
    Clean:    "hello world"  (single space)
    Map:      [0,1,2,3,4,5,6,7,...]  (position 6 in clean = position 7 in original)
    """
    clean_text: str
    original_text: str
    position_map: List[int]  # clean_pos -> original_pos
    whitespace_map: WhitespaceMap


# ============================================================================
# LAYER 1: STRING CLEANER - The Foundation
# ============================================================================

class StringCleaner:
    """
    Normalizes strings and identifies whitespace issues
    
    Philosophy: Separate whitespace concerns from character concerns.
    This allows the DiffEngine to focus purely on character-level changes.
    """
    
    @staticmethod
    def analyze(text: str) -> CleanString:
        """
        Clean the string and map all whitespace issues
        
        Returns:
            CleanString with normalized text and full whitespace tracking
        """
        whitespace_map = WhitespaceMap(
            leading_spaces=[],
            trailing_spaces=[],
            double_spaces=[],
            tabs=[]
        )
        
        # Detect leading spaces
        i = 0
        while i < len(text) and text[i] == ' ':
            whitespace_map.leading_spaces.append(i)
            i += 1
        
        # Detect trailing spaces
        i = len(text) - 1
        while i >= 0 and text[i] == ' ':
            whitespace_map.trailing_spaces.append(i)
            i -= 1
        
        # Detect double spaces and tabs
        i = 0
        while i < len(text):
            if text[i] == '\t':
                whitespace_map.tabs.append(i)
            elif text[i] == ' ' and i + 1 < len(text) and text[i + 1] == ' ':
                # Found double space - count the run
                start = i
                while i < len(text) and text[i] == ' ':
                    i += 1
                end = i
                whitespace_map.double_spaces.append((start, end))
                continue
            i += 1
        
        # Create clean version (normalize all whitespace to single spaces)
        clean_text = ' '.join(text.split())
        
        # Build position map (clean_pos -> original_pos)
        position_map = []
        clean_idx = 0
        original_idx = 0
        
        while original_idx < len(text):
            if text[original_idx] not in ' \t\n':
                position_map.append(original_idx)
                clean_idx += 1
            original_idx += 1
        
        return CleanString(
            clean_text=clean_text,
            original_text=text,
            position_map=position_map,
            whitespace_map=whitespace_map
        )


# ============================================================================
# LAYER 2: DIFF ENGINE - The Intelligence (with Look-Ahead Buffer!)
# ============================================================================

class DiffEngine:
    """
    Semantic difference detection with look-ahead buffer
    
    Philosophy: Don't just return raw edit operations. Return human-meaningful
    semantic edits that explain WHAT changed, not just HOW to transform one
    string into another.
    
    The Look-Ahead Buffer:
    ----------------------
    When we encounter a DELETE operation, we PEEK at the next operation.
    If it's an INSERT of the same character at an adjacent position, we
    CONSUME both operations and emit a TRANSPOSITION.
    
    This is the elegant solution the Auditor recommended!
    """
    
    @staticmethod
    def analyze(correct_text: str, problem_text: str) -> List[SemanticEdit]:
        """
        Analyze differences and return semantic edits
        
        Args:
            correct_text: What it should be
            problem_text: What it actually is
            
        Returns:
            List of semantic edits (TRANSPOSITION, TYPO, DELETION, etc)
        """
        from rapidfuzz import distance
        
        # Get raw Levenshtein operations
        ops = distance.Levenshtein.editops(correct_text, problem_text)
        ops_list = [(op.tag, op.src_pos, op.dest_pos) for op in ops]
        
        semantic_edits = []
        i = 0
        
        # THE LOOK-AHEAD BUFFER (Auditor's recommendation!)
        while i < len(ops_list):
            op_type, src_pos, dest_pos = ops_list[i]
            
            # LOOK AHEAD: Check if this is part of a transposition
            if i + 1 < len(ops_list):
                next_op_type, next_src_pos, next_dest_pos = ops_list[i + 1]
                
                # Pattern: INSERT + DELETE (Levenshtein's transposition signature)
                if op_type == 'insert' and next_op_type == 'delete':
                    transposition = DiffEngine._check_transposition(
                        correct_text, problem_text,
                        src_pos, dest_pos, next_src_pos, next_dest_pos
                    )
                    
                    if transposition:
                        semantic_edits.append(transposition)
                        i += 2  # CONSUME both operations
                        continue
            
            # Not a transposition - process as normal edit
            if op_type == 'delete':
                # True deletion - character missing
                if src_pos < len(correct_text):
                    correct_char = correct_text[src_pos]
                    if correct_char not in ' \t\n':  # Skip whitespace deletions
                        semantic_edits.append(SemanticEdit(
                            edit_type=EditType.DELETION,
                            position=dest_pos,
                            correct_char=correct_char,
                            problem_char=''
                        ))
            
            elif op_type == 'replace':
                # Typo - wrong character
                if (src_pos < len(correct_text) and dest_pos < len(problem_text)):
                    correct_char = correct_text[src_pos]
                    problem_char = problem_text[dest_pos]
                    if correct_char not in ' \t\n' and problem_char not in ' \t\n':
                        semantic_edits.append(SemanticEdit(
                            edit_type=EditType.TYPO,
                            position=dest_pos,
                            correct_char=correct_char,
                            problem_char=problem_char
                        ))
            
            elif op_type == 'insert':
                # Extra character
                if dest_pos < len(problem_text):
                    problem_char = problem_text[dest_pos]
                    if problem_char not in ' \t\n':
                        semantic_edits.append(SemanticEdit(
                            edit_type=EditType.INSERTION,
                            position=dest_pos,
                            correct_char='',
                            problem_char=problem_char
                        ))
            
            i += 1
        
        return semantic_edits
    
    @staticmethod
    def _check_transposition(correct_text: str, problem_text: str,
                           src_pos: int, dest_pos: int,
                           next_src_pos: int, next_dest_pos: int) -> Optional[SemanticEdit]:
        """
        Check if INSERT + DELETE pair is actually a transposition
        
        Safety checks (from Auditor feedback):
        1. Characters must be adjacent in source
        2. Characters must NOT be whitespace
        3. Characters must be swapped (same letters, different order)
        
        Returns:
            SemanticEdit with TRANSPOSITION type, or None if not a transposition
        """
        # Bounds checking
        if not (src_pos < len(correct_text) and src_pos + 1 < len(correct_text) and
                dest_pos < len(problem_text) and dest_pos + 1 < len(problem_text)):
            return None
        
        # Get the characters
        correct_char_1 = correct_text[src_pos]
        correct_char_2 = correct_text[src_pos + 1]
        problem_char_1 = problem_text[dest_pos]
        problem_char_2 = problem_text[dest_pos + 1]
        
        # SAFETY CHECK 1: Must be adjacent in source
        if next_src_pos != src_pos + 1:
            return None
        
        # SAFETY CHECK 2: Must NOT be whitespace
        if correct_char_1 in ' \t\n' or correct_char_2 in ' \t\n':
            return None
        
        # SAFETY CHECK 3: Characters must be swapped
        if correct_char_1 == problem_char_2 and correct_char_2 == problem_char_1:
            # IT'S A TRANSPOSITION! 🎉
            return SemanticEdit(
                edit_type=EditType.TRANSPOSITION,
                position=dest_pos,
                correct_char=correct_char_1,
                problem_char=problem_char_1,
                pair_position=dest_pos + 1
            )
        
        return None


# ============================================================================
# LAYER 3: ANNOTATOR - The Business Rules
# ============================================================================

class Annotator:
    """
    Decides when to show inline annotations like [missing v]
    
    Philosophy: Annotations are for truly missing characters, NOT for
    transpositions where the character is just in the wrong place.
    """
    
    @staticmethod
    def build_annotations(semantic_edits: List[SemanticEdit]) -> List[Tuple[int, str]]:
        """
        Build inline annotations for missing characters
        
        Business Rule: Only show [missing X] for DELETION edits.
        Transpositions get NO annotation (just visual highlighting).
        
        Returns:
            List of (position, annotation_text) tuples
        """
        annotations = []
        
        for edit in semantic_edits:
            if edit.edit_type == EditType.DELETION:
                # True deletion - show [missing X]
                annotation = f'[missing {edit.correct_char}]'
                annotations.append((edit.position, annotation))
        
        return annotations


# ============================================================================
# LAYER 4: HTML RENDERER - The Presentation
# ============================================================================

class HtmlRenderer:
    """
    Renders beautiful Scandinavian-style HTML with proper color coding
    
    Philosophy: Clean, minimal, professional. Let the design tokens guide us.
    """
    
    # Design tokens (from our Scandinavian design system)
    COLOR_TYPO = "#fee2e2"          # Pink/red for character issues
    COLOR_TYPO_TEXT = "#991b1b"     # Dark red text
    COLOR_WHITESPACE = "#fff3e0"    # Orange for whitespace
    COLOR_WHITESPACE_TEXT = "#c2410c"  # Dark orange text
    COLOR_ANNOTATION = "#dc2626"    # Red for [missing X]
    
    @staticmethod
    def render(problem_text: str, 
              semantic_edits: List[SemanticEdit],
              annotations: List[Tuple[int, str]],
              whitespace_map: WhitespaceMap) -> str:
        """
        Render gorgeous HTML with highlights and annotations
        
        Args:
            problem_text: The actual text (with problems)
            semantic_edits: Semantic understanding of what's wrong
            annotations: Inline [missing X] annotations
            whitespace_map: Whitespace issues to highlight
            
        Returns:
            Beautiful HTML string
        """
        result = []
        
        # Build position maps
        typo_positions = set()
        transposition_positions = set()
        annotation_map = {pos: text for pos, text in annotations}
        
        for edit in semantic_edits:
            if edit.edit_type == EditType.TRANSPOSITION:
                transposition_positions.add(edit.position)
                if edit.pair_position:
                    transposition_positions.add(edit.pair_position)
            elif edit.edit_type in (EditType.TYPO, EditType.INSERTION):
                typo_positions.add(edit.position)
        
        # Render character by character
        i = 0
        while i < len(problem_text):
            char = problem_text[i]
            
            # Insert inline annotations BEFORE the character
            if i in annotation_map:
                result.append(HtmlRenderer._render_annotation(annotation_map[i]))
            
            # Check for whitespace issues
            if HtmlRenderer._is_whitespace_issue(i, whitespace_map):
                result.append(HtmlRenderer._render_whitespace(char))
                i += 1
                continue
            
            # Check for character issues (typos/transpositions)
            if i in typo_positions or i in transposition_positions:
                # Find the chunk (consecutive issues)
                chunk_start = i
                chunk_end = i + 1
                while (chunk_end < len(problem_text) and 
                       (chunk_end in typo_positions or chunk_end in transposition_positions)):
                    chunk_end += 1
                
                # Render the chunk
                chunk_text = problem_text[chunk_start:chunk_end]
                result.append(HtmlRenderer._render_typo_chunk(chunk_text))
                i = chunk_end
                continue
            
            # Normal character
            result.append(char)
            i += 1
        
        # Add any trailing annotations
        if len(problem_text) in annotation_map:
            result.append(HtmlRenderer._render_annotation(annotation_map[len(problem_text)]))
        
        return ''.join(result)
    
    @staticmethod
    def _is_whitespace_issue(pos: int, whitespace_map: WhitespaceMap) -> bool:
        """Check if this position has a whitespace issue"""
        if pos in whitespace_map.leading_spaces:
            return True
        if pos in whitespace_map.trailing_spaces:
            return True
        if pos in whitespace_map.tabs:
            return True
        for start, end in whitespace_map.double_spaces:
            if start < pos < end:  # Don't highlight the FIRST space (it's correct)
                return True
        return False
    
    @staticmethod
    def _render_typo_chunk(text: str) -> str:
        """Render a chunk of characters with typo highlighting"""
        return (f'<span style="background-color: {HtmlRenderer.COLOR_TYPO}; '
                f'color: {HtmlRenderer.COLOR_TYPO_TEXT}; '
                f'padding: 2px 4px; border-radius: 3px; font-weight: 500;">'
                f'{text}</span>')
    
    @staticmethod
    def _render_whitespace(char: str) -> str:
        """Render whitespace with orange highlighting"""
        return (f'<span style="background-color: {HtmlRenderer.COLOR_WHITESPACE}; '
                f'color: {HtmlRenderer.COLOR_WHITESPACE_TEXT}; '
                f'padding: 2px 4px; border-radius: 3px; font-weight: 500;">'
                f'{char}</span>')
    
    @staticmethod
    def _render_annotation(text: str) -> str:
        """Render inline [missing X] annotation"""
        return (f'<span style="color: {HtmlRenderer.COLOR_ANNOTATION}; '
                f'font-size: 11px; font-weight: 400;">{text}</span>')


# ============================================================================
# PUBLIC API - The Main Entry Point
# ============================================================================

def highlight_differences(correct_text: str, problem_text: str) -> str:
    """
    The beautiful mille-feuille - all layers working together!
    
    This is the ONLY function that external code needs to call.
    Everything else is beautifully encapsulated.
    
    Args:
        correct_text: What the text should be
        problem_text: What the text actually is
        
    Returns:
        Gorgeous HTML with Scandinavian highlighting
        
    Example:
        >>> correct = "Costs and expenses - Audit"
        >>> problem = "Costs and expesnes  - Audit"
        >>> html = highlight_differences(correct, problem)
        >>> # Returns: "Costs and expe<span...>sn</span>es  - Audit"
    """
    # Layer 1: Clean and analyze whitespace
    clean_correct = StringCleaner.analyze(correct_text)
    clean_problem = StringCleaner.analyze(problem_text)
    
    # Layer 2: Get semantic edits (with look-ahead buffer!)
    semantic_edits = DiffEngine.analyze(clean_correct.clean_text, clean_problem.clean_text)
    
    # Layer 3: Build annotations (suppress for transpositions)
    annotations = Annotator.build_annotations(semantic_edits)
    
    # Layer 4: Render gorgeous HTML
    html = HtmlRenderer.render(
        problem_text,
        semantic_edits,
        annotations,
        clean_problem.whitespace_map
    )
    
    return html


# ============================================================================
# TESTING UTILITIES (for development)
# ============================================================================

def debug_semantic_edits(correct_text: str, problem_text: str) -> None:
    """
    Debug helper to see what semantic edits are detected
    
    Useful during development to verify the look-ahead buffer works!
    """
    clean_correct = StringCleaner.analyze(correct_text)
    clean_problem = StringCleaner.analyze(problem_text)
    
    edits = DiffEngine.analyze(clean_correct.clean_text, clean_problem.clean_text)
    
    print(f"\n{'='*60}")
    print(f"Correct: '{correct_text}'")
    print(f"Problem: '{problem_text}'")
    print(f"\nSemantic Edits ({len(edits)} total):")
    for edit in edits:
        print(f"  {edit}")
    print(f"{'='*60}\n")
