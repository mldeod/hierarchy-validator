# Analytics Accelerator - Module Standards Guide

**Version:** 1.0  
**Last Updated:** December 2024  
**Author:** Manu Lopez

---

## Philosophy

The Analytics Accelerator follows Apple's design philosophy: **minimal, elegant, and functional**. Every module should feel like part of a cohesive product, not a collection of separate tools.

**Core Principles:**
- **Consistency over novelty** - Users should instantly understand any new module
- **Function over decoration** - No emojis, no unnecessary flourishes
- **Professional grade** - Enterprise-ready quality for mid-market pricing
- **Modular architecture** - Each module is independent but shares common patterns

---

## Module Structure

### File Organization

Every module follows this structure:

```
modules/
└── your_module_name/
    ├── __init__.py          # Module initialization
    ├── ui.py                # User interface (Streamlit)
    ├── engine.py            # Core logic/algorithms
    └── README.md            # Module documentation
```

**Key Files:**

**`ui.py`** - The interface layer
- Contains `render(workflow_data=None)` function
- Handles all Streamlit UI elements
- Manages session state
- No business logic (call engine.py instead)

**`engine.py`** - The business logic
- Pure Python functions
- No Streamlit imports
- Testable independently
- Reusable across modules

### Naming Conventions

**Module Names:**
- Lowercase with underscores: `tree_converter`, `hierarchy_validator`
- Descriptive and specific: `budget_allocator` not `allocator`

**Function Names:**
- Descriptive verbs: `find_orphans()`, `validate_hierarchy()`, `convert_tree()`
- Not generic: `process()`, `do_thing()`, `handle()`

**File Names:**
- Always lowercase: `ui.py`, `engine.py`, `validation_engine.py`
- No version numbers in filenames: `ui_v2.py` ❌ → `ui.py` ✅

---

## UI Standards

### Layout Structure

Every module follows this vertical flow:

```
1. [Main header from main.py - "Analytics Accelerator"]
2. [Tab selection]
3. [Module content begins]
   - File upload OR workflow data
   - Action button (if needed)
   - Results display
   - Download options
```

**❌ DO NOT:**
- Add a second header with the module name (main.py already shows it in the ribbon)
- Create custom layouts that break the flow

**✅ DO:**
- Start directly with functionality
- Use markdown headers (`###`) for sections within your module
- Add separator lines (`st.markdown("---")`) between major sections

### Button Standards

**All buttons use BLUE theme:**

```python
if st.button("Action Name", type="primary", use_container_width=True):
    # Your code here
```

**Button Text:**
- Action-oriented: "Convert Tree", "Validate Hierarchy", "Generate Report"
- Not generic: "Submit", "Go", "Process"
- Capitalized: "Convert Tree" not "convert tree"

**When to Use Buttons:**
- User needs to explicitly trigger an action
- Processing takes >1 second
- Results should persist until next action

**When NOT to Use Buttons:**
- Auto-run on file upload is acceptable if processing is instant (<1 sec)
- Use session state to prevent re-running on every interaction

### KPI Pills/Badges

**Standard Badge Style:**

```python
badges_html = f'''
<div style="text-align: center; margin: 20px 0;">
    <span class="summary-badge" style="background: #e3f2fd; color: #1565c0;">
        {value} Label Text
    </span>
    <span class="summary-badge badge-warning">{warnings} Warnings</span>
    <span class="summary-badge badge-error">{errors} Errors</span>
</div>
'''
st.markdown(badges_html, unsafe_allow_html=True)
```

**Badge Order (always consistent):**
1. Info metrics (blue) - Descriptive counts
2. Warnings (orange) - Non-critical issues
3. Errors (red) - Critical issues

**Example - Tree Converter:**
```
[2 Total Members] [1 Max Depth] [1 Leaf Nodes] [1 Warnings] [2 Errors]
```

**Example - Hierarchy Validator:**
```
[422 Members Checked] [45 Issues Found] [32 Warnings] [13 Errors]
```

### Separator Lines

Use `st.markdown("---")` to create visual breaks between sections:

```python
# After file upload
st.markdown("---")

# Before results display
st.markdown("---")

# After KPI badges
st.markdown("---")
```

**Spacing:**
- One blank line before and after in code
- Creates clean visual hierarchy
- Helps users scan the interface

### Color System

**Information (Blue):**
- Background: `#e3f2fd`
- Text: `#1565c0`
- Use for: Neutral counts, informational metrics

**Warning (Orange):**
- Badge class: `badge-warning`
- Background: `#fff4e5`
- Text: `#f57c00`
- Use for: Non-critical issues that should be reviewed

**Error (Red):**
- Badge class: `badge-error`
- Background: `#ffe5e5`
- Text: `#d32f2f`
- Use for: Critical issues that must be fixed

**Success (Green):**
- Badge class: `badge-success`
- Background: `#e8f5e9`
- Text: `#388e3c`
- Use for: Completion states, validation passes

**Never:**
- Use emojis in production UI
- Use custom colors outside this system
- Mix color meanings (red for info, blue for errors, etc.)

---

## Code Patterns

### Session State Management

Always use session state for data that persists across interactions:

```python
# Initialize at module start
if 'module_results' not in st.session_state:
    st.session_state.module_results = None

# Store results after processing
if st.button("Run Analysis"):
    results = process_data(df)
    st.session_state.module_results = results

# Display results if they exist
if st.session_state.module_results is not None:
    display_results(st.session_state.module_results)
```

**Key session state variables:**
- `{module}_results` - Analysis output
- `{module}_file_key` - File uploader key (for reset)
- `{module}_workflow_data` - Data from other modules

### Workflow Integration

Every module should accept data from other modules:

```python
def render(workflow_data=None):
    """
    Render the module UI
    
    Args:
        workflow_data: DataFrame passed from another module (optional)
    """
    
    # Check for workflow data first
    if workflow_data is not None:
        df = workflow_data
        st.success("Data received from previous module")
    else:
        # File upload as alternative
        uploaded_file = st.file_uploader(...)
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
```

**Passing data between modules:**

```python
# In sending module (e.g., Tree Converter)
if st.button("→ Send to Validator"):
    send_workflow_data('hierarchy_validator', converted_df)
    st.success("Data sent to Hierarchy Validator!")
    
# In receiving module (e.g., Hierarchy Validator)
# Automatically receives via workflow_data parameter
```

### Error Handling

Always wrap file operations and data processing:

```python
try:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    # Validate required columns
    required_cols = ['_member_name', '_parent_name']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Missing required columns: {', '.join(required_cols)}")
        return
        
    # Process data
    results = process_data(df)
    
except Exception as e:
    st.error(f"Error processing file: {str(e)}")
    return
```

**Error Message Guidelines:**
- Be specific: "Missing column '_member_name'" not "Invalid data"
- Be helpful: Suggest what the user should do
- Be professional: No "Oops!" or casual language

### Loading States

Always show progress for operations >1 second:

```python
with st.spinner("Analyzing hierarchy..."):
    results = long_running_analysis(df)

st.success("Analysis complete!")
```

**Spinner text should be:**
- Present continuous: "Analyzing...", "Converting...", "Validating..."
- Specific to the action
- Professional tone

---

## File Handling

### Upload Patterns

Standard file uploader configuration:

```python
uploaded_file = st.file_uploader(
    "Upload your file",
    type=['xlsx', 'xls', 'csv'],
    help="Supported formats: Excel (.xlsx, .xls) and CSV",
    key=f"uploader_{st.session_state.file_key}"
)
```

**File type support:**
- Always support both Excel (.xlsx, .xls) and CSV
- Handle encoding issues gracefully
- Show clear error messages for unsupported formats

### Download Patterns

Use Streamlit's download button:

```python
# For DataFrames
csv = df.to_csv(index=False)
st.download_button(
    label="Download Results (CSV)",
    data=csv,
    file_name="results.csv",
    mime="text/csv"
)

# For Excel files
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Results')
buffer.seek(0)

st.download_button(
    label="Download Results (Excel)",
    data=buffer,
    file_name="results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

**Download button text:**
- Include format: "Download (CSV)", "Download (Excel)"
- Include content: "Download Results", "Download Converted Tree"
- Professional: Not "Get File" or "Download Now!"

---

## Data Display

### Tables

Use Streamlit's native dataframe with column configuration:

```python
st.dataframe(
    df,
    hide_index=True,
    use_container_width=True,
    column_config={
        'Issue': st.column_config.TextColumn('Issue', width='small'),
        'Member Name': st.column_config.TextColumn('Member Name', width='large'),
        'Count': st.column_config.NumberColumn('Count', width='small')
    }
)
```

**Column width guidelines:**
- `width='small'` - IDs, numbers, short codes (50-100px)
- `width='medium'` - Categories, short text (150-200px)
- `width='large'` - Names, descriptions (300-400px)
- Default - Let Streamlit decide

### Data Preview

Always show a preview after loading:

```python
st.markdown("---")
st.markdown("#### Data Preview")
st.dataframe(df.head(10), use_container_width=True)
st.markdown(f"**Loaded:** {len(df):,} rows × {len(df.columns)} columns")
```

**Preview size:**
- 10 rows for most cases
- 20 rows if data is simple/narrow
- 5 rows if data is very wide (>10 columns)

---

## Testing Checklist

Before pushing any module to GitHub:

### Functionality
- [ ] File upload works (Excel and CSV)
- [ ] All buttons trigger correctly
- [ ] Results display properly
- [ ] Download buttons generate valid files
- [ ] Error messages show for invalid input

### UI/UX
- [ ] No duplicate headers
- [ ] Blue buttons (not green)
- [ ] KPI badges match standard order (Info → Warning → Error)
- [ ] Separator lines between sections
- [ ] No emojis in UI
- [ ] Consistent spacing

### Integration
- [ ] Module works standalone (via file upload)
- [ ] Module works with workflow data (if applicable)
- [ ] Data can be sent to other modules (if applicable)
- [ ] Session state properly initialized

### Performance
- [ ] No auto-rerun loops
- [ ] Large files don't crash (<5MB works smoothly)
- [ ] Spinner shows for operations >1 second
- [ ] Results cached appropriately

### Code Quality
- [ ] No syntax errors (`python3 -m py_compile file.py`)
- [ ] Proper indentation (4 spaces, no tabs)
- [ ] Descriptive variable names
- [ ] Comments for complex logic
- [ ] No debug print statements

---

## Git Workflow

### Branch Strategy

**Main branch:** Production-ready code only
**Feature branches:** Individual module development

```bash
# Create feature branch
git checkout -b feature/new-module-name

# Work on your module
# ... make changes ...

# Commit frequently
git add .
git commit -m "Add validation logic"

# Push feature branch
git push -u origin feature/new-module-name

# Merge to main when ready
git checkout main
git merge feature/new-module-name
git push
```

### Commit Messages

Follow this format:

```
TYPE: Brief description (50 chars max)

Detailed explanation if needed
- What changed
- Why it changed
- Any breaking changes
```

**Types:**
- `FEAT:` New feature or module
- `FIX:` Bug fix
- `UI:` UI/UX improvements
- `REFACTOR:` Code restructuring (no behavior change)
- `DOCS:` Documentation updates
- `STYLE:` Formatting, no code change

**Examples:**
```bash
git commit -m "FEAT: Add budget allocation module"
git commit -m "FIX: Resolve duplicate header in validator"
git commit -m "UI: Standardize KPI pills across all modules"
git commit -m "REFACTOR: Extract validation functions to engine.py"
```

### Deployment Process

1. **Test Locally:**
   ```bash
   cd ~/projects/hierarchy-validator
   streamlit run main.py
   ```
   Test all functionality thoroughly

2. **Check Files:**
   ```bash
   git status
   git diff
   ```
   Review all changes before committing

3. **Commit & Push:**
   ```bash
   git add [specific files]
   git commit -m "TYPE: Description"
   git push
   ```

4. **Wait for Deployment:**
   - Streamlit Cloud auto-deploys in 1-2 minutes
   - Check deployment logs if issues arise

5. **Test Production:**
   - Visit live URL
   - Test all modules
   - Verify no errors in production

---

## Common Pitfalls

### Indentation Hell
**Problem:** Python indentation errors break the entire app

**Solution:**
- Use 4 spaces (never tabs)
- Use an editor with visible whitespace
- Test with `python3 -m py_compile file.py` before pushing
- When in doubt, start from a working file and make small changes

### Session State Scope
**Problem:** Variables disappear or cause "not defined" errors

**Solution:**
```python
# WRONG - variable only exists inside button
if st.button("Process"):
    results = process_data(df)

# Show results here - ERROR! results doesn't exist
st.write(results)

# RIGHT - use session state
if st.button("Process"):
    st.session_state.results = process_data(df)

# Now it exists outside the button
if st.session_state.results is not None:
    st.write(st.session_state.results)
```

### File Download Issues
**Problem:** Downloaded files are corrupted or empty

**Solution:**
- Always use `BytesIO` for binary files (Excel)
- Always call `buffer.seek(0)` before download
- Use correct MIME types
- Test downloads with different file sizes

### Styling Inconsistency
**Problem:** New module looks different from others

**Solution:**
- Copy UI patterns from existing modules
- Use shared CSS from `styling.py`
- Check badge colors match the standard
- Verify button color is blue (not green)
- Use the same separator lines

---

## Adding a New Module

**Step-by-step process:**

1. **Create Module Structure:**
   ```bash
   mkdir -p modules/your_module_name
   touch modules/your_module_name/__init__.py
   touch modules/your_module_name/ui.py
   touch modules/your_module_name/engine.py
   ```

2. **Register Module:**
   Edit `config/modules_config.py`:
   ```python
   AVAILABLE_MODULES = {
       # ... existing modules ...
       'your_module_name': {
           'title': 'Your Module Display Name',
           'enabled': True
       }
   }
   ```

3. **Create UI Shell:**
   Start with this template in `ui.py`:
   ```python
   import streamlit as st
   import pandas as pd
   
   def render(workflow_data=None):
       """Your module UI"""
       
       st.markdown("### Your Module Name")
       
       # File upload or workflow data
       if workflow_data is not None:
           df = workflow_data
       else:
           uploaded_file = st.file_uploader(
               "Upload file", 
               type=['xlsx', 'xls', 'csv']
           )
           if uploaded_file:
               df = pd.read_excel(uploaded_file)
       
       # Your module logic here
   ```

4. **Add Business Logic:**
   Create functions in `engine.py`:
   ```python
   import pandas as pd
   
   def process_data(df):
       """Core processing function"""
       # Your logic here
       return results
   ```

5. **Test Locally:**
   ```bash
   streamlit run main.py
   ```

6. **Follow Standards:**
   - Use blue buttons
   - Add KPI badges
   - Include separator lines
   - Handle errors gracefully

7. **Deploy:**
   ```bash
   git add modules/your_module_name/
   git add config/modules_config.py
   git commit -m "FEAT: Add your module name"
   git push
   ```

---

## Resources

### Documentation
- Streamlit Docs: https://docs.streamlit.io
- Pandas Docs: https://pandas.pydata.org/docs
- Python Style Guide: https://pep8.org

### Internal Files
- `shared/styling.py` - CSS and styling functions
- `config/modules_config.py` - Module registration
- `shared/workflow.py` - Inter-module data passing

### Getting Help
- Check existing modules for patterns
- Review this standards guide
- Test locally before pushing
- Ask questions in team chat

---

## Version History

**v1.0 (December 2024)**
- Initial standards document
- Covers Tree Converter and Hierarchy Validator patterns
- Establishes blue theme, pill standards, and code patterns

---

**Remember:** Consistency is more important than perfection. When in doubt, copy what works from existing modules!
