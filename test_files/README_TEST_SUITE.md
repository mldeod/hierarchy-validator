# Tree Converter Test Suite

This folder contains 10 test files to validate the Tree Converter's error handling capabilities.

## 📋 Test Files

### ✅ Valid Trees (Should Pass)

**TEST_01_perfect_tree.xlsx**
- Description: Perfect valid hierarchy
- Expected: 0 errors, 0 warnings
- Structure: Simple 2-level tree

**TEST_07_mixed_operators.xlsx**
- Description: Real P&L structure with contra accounts
- Expected: 0 errors, 0 warnings
- Operators: Mix of `+` and `-` (Returns, Discounts as contra)

**TEST_09_max_depth.xlsx**
- Description: Tests maximum depth (10 levels)
- Expected: 0 errors, 0 warnings
- Structure: L1 → L2 → L3 → ... → L10

---

### ⚠️ Warning Cases (Should Work But Flag Issues)

**TEST_02_two_root_nodes.xlsx**
- Description: Two separate trees (Assets & Liabilities)
- Expected: 0 errors, possibly 1 warning (unusual structure)
- Notes: Technically valid in Vena (separate shared members)

**TEST_05_duplicate_members.xlsx**
- Description: "USA" appears under both North America and Europe
- Expected: 0 errors, 1 warning (shared member)
- Notes: Valid in Vena - creates shared member

**TEST_06_invalid_operators.xlsx**
- Description: Contains invalid operators (`x`, `*`)
- Expected: 0 errors, 2 warnings (invalid operators)
- Behavior: Should default to `+`

**TEST_08_whitespace_issues.xlsx**
- Description: Empty rows, leading/trailing spaces
- Expected: 0 errors, 0 warnings (auto-cleaned)
- Behavior: Should skip empty rows, trim whitespace

---

### ❌ Error Cases (Should Fail)

**TEST_03_skipped_level.xlsx**
- Description: Jumps from Level 1 → Level 3 (skips Level 2)
- Expected: 1 error (skipped level)
- Member: "PROBLEM"

**TEST_04_missing_parent.xlsx**
- Description: Level 3 member with no Level 2 parent
- Expected: 1 error (missing parent)
- Member: "Orphan Product"

---

### 💥 Stress Test

**TEST_10_chaos_mode.xlsx**
- Description: Everything that can go wrong
- Expected: Multiple errors and warnings
- Issues:
  - 2 root nodes
  - Invalid operator
  - Skipped level
  - Missing parent (orphan)
  - Duplicate member
  - Empty rows

---

## 🧪 How to Test

1. **Run the app:**
   ```bash
   streamlit run main.py
   ```

2. **Go to Tree Converter tab**

3. **Upload each test file**

4. **Verify results:**
   - Check error count matches expected
   - Read error messages for clarity
   - Verify warnings are helpful
   - Ensure valid trees process correctly

---

## ✅ Expected Behavior

### Error Handling
- **File errors:** Clear message if file can't be read
- **Skipped levels:** Specific row and level numbers
- **Missing parents:** Identifies which parent is missing
- **Invalid operators:** Warns and defaults to `+`

### Tree Processing
- **Empty rows:** Automatically skipped
- **Whitespace:** Automatically trimmed
- **Duplicates:** Treated as shared members (tree uses first occurrence for navigation)
- **Multiple roots:** Allowed (creates separate subtrees)

### Output Quality
- **Error messages** should include:
  - Row number (Excel row)
  - Member name
  - Specific problem
  - What was expected

---

## 📊 Test Results Matrix

| Test File | Errors | Warnings | Should Convert | Notes |
|-----------|--------|----------|----------------|-------|
| TEST_01   | 0      | 0        | ✅ Yes         | Baseline |
| TEST_02   | 0      | 0-1      | ✅ Yes         | Multiple roots OK |
| TEST_03   | 1      | 0        | ❌ No          | Skipped level |
| TEST_04   | 1      | 0        | ❌ No          | Missing parent |
| TEST_05   | 0      | 1        | ✅ Yes         | Shared member |
| TEST_06   | 0      | 2        | ✅ Yes         | Invalid ops → + |
| TEST_07   | 0      | 0        | ✅ Yes         | Real P&L |
| TEST_08   | 0      | 0        | ✅ Yes         | Auto-cleaned |
| TEST_09   | 0      | 0        | ✅ Yes         | Max depth |
| TEST_10   | 3+     | 2+       | ❌ No          | Multiple issues |

---

## 🎯 Success Criteria

**Parser should:**
- ✅ Catch all errors before conversion
- ✅ Provide helpful, specific error messages
- ✅ Handle edge cases gracefully
- ✅ Auto-fix minor issues (whitespace)
- ✅ Warn about unusual patterns (duplicates, invalid ops)
- ✅ Process valid trees correctly

**UI should:**
- ✅ Display error count prominently
- ✅ Show errors in readable format
- ✅ Include row numbers for easy fixing
- ✅ Prevent download if errors exist
- ✅ Allow download if only warnings

---

## 🔧 Troubleshooting

If a test fails unexpectedly:

1. **Check error message** - Is it clear and actionable?
2. **Verify row numbers** - Do they match Excel (1-indexed)?
3. **Review expected behavior** - Is the parser too strict/lenient?
4. **Update test** - If requirements changed

---

## 📝 Notes

- All test files include header row (Row 1)
- Data starts at Row 2
- Column L contains operators
- Empty cells represented as `None` in code
- Excel row numbers = data row + 1 (for header)

---

**Created:** December 2024  
**Last Updated:** December 2024  
**Version:** 1.0
