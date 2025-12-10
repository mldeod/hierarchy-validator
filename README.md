# Hierarchy Validator

**Professional FP&A tool for validating and converting Excel hierarchy trees into Vena-compatible formats.**

Built for mid-market companies who need enterprise-grade hierarchy management without enterprise complexity.

---

## 🚀 Features

### Tree Converter
- **Visual Tree → Parent-Child Conversion**: Upload Excel hierarchies in visual tree format, get Vena-compatible 6-column output
- **Smart Validation**: Detects structural issues (skipped levels, missing parents, multiple roots)
- **Duplicate Detection**: Identifies and handles shared members across branches
- **Custom Tree Visualization**: Shows all members including duplicates with clear "(shared)" markers
- **Operator Support**: Handles +, -, ~ operators for additive, contra, and ignored rollups
- **Actionable Error Messages**: Every error tells you exactly what's wrong and how to fix it

### Hierarchy Validator
- **Coming Soon**: Validate existing parent-child hierarchies
- **Circular Reference Detection**: Find and fix circular dependencies
- **Orphan Detection**: Identify members without valid parents
- **Depth Analysis**: Ensure consistent hierarchy depth

---

## 📋 Requirements

```
streamlit>=1.28.0
pandas>=2.0.0
openpyxl>=3.1.0
treelib>=1.6.1
```

---

## 🛠️ Installation

### Option 1: Local Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/hierarchy-validator.git
cd hierarchy-validator

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run main.py
```

### Option 2: Streamlit Cloud

1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Deploy directly from your GitHub repository
4. Done! Your app is live

---

## 📖 Usage

### Tree Converter

1. **Enter Dimension Name**: Specify your Vena dimension (e.g., Account, Cost Center, Products)

2. **Upload Excel File**: Use the visual tree format:
   - Columns A-J: Hierarchy levels (position = level)
   - Column K: Member alias (optional)
   - Column L: Operator (+, -, or ~)

3. **Convert**: Click "Convert Tree" to process

4. **Review**: Check statistics, warnings, and tree visualization

5. **Download**: Get your Vena-compatible CSV file

### Input Format Example

```
Level 1    Level 2           Level 3    ...    Alias    Operator
Total                                            ROOT     +
           North America                         NA       +
                             USA                 USA      +
                             Canada              CAN      +
           Europe                                EU       +
                             Germany             DE       +
                             France              FR       +
```

### Output Format

```csv
_dim,_member_name,_member_alias,_parent_name,_operator,_cmd
Account,Total,ROOT,,+,+
Account,North America,NA,Total,+,+
Account,USA,USA,North America,+,+
Account,Canada,CAN,North America,+,+
Account,Europe,EU,Total,+,+
Account,Germany,DE,Europe,+,+
Account,France,FR,Europe,+,+
```

---

## 🧪 Testing

The project includes 10 comprehensive test files covering:

- ✅ Perfect valid trees
- ✅ Multiple root nodes
- ✅ Skipped hierarchy levels
- ✅ Missing parents
- ✅ Duplicate/shared members
- ✅ Invalid operators
- ✅ Mixed operator scenarios
- ✅ Whitespace handling
- ✅ Maximum depth (10 levels)
- ✅ Chaos mode (everything at once)

Test files are located in `/test_files/` with detailed documentation in `README_TEST_SUITE.md`.

---

## 🎨 Design Philosophy

**Apple-Minimalist Aesthetic**
- Clean, professional interface
- Elegant color coding (green for success, blue for info, yellow for warnings, red for errors)
- Subtle animations and interactions
- Mobile-responsive design

**User-Friendly Error Handling**
- Every error explains what's wrong
- Clear guidance on how to fix it
- No technical jargon

**Production-Ready Code**
- Modular architecture
- Comprehensive validation
- Detailed logging
- Easy to extend

---

## 📁 Project Structure

```
hierarchy-validator/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── config/
│   ├── modules_config.py           # Module configuration
│   └── __init__.py
│
├── modules/
│   ├── tree_converter/             # Tree → Parent-Child converter
│   │   ├── engine.py               # Core parsing logic
│   │   ├── ui.py                   # Streamlit interface
│   │   └── __init__.py
│   │
│   └── hierarchy_validator/        # Parent-Child validator (coming soon)
│       ├── validation_engine.py
│       ├── ui.py
│       └── __init__.py
│
├── shared/
│   ├── styling.py                  # Unified CSS/design system
│   ├── workflow.py                 # Common workflow functions
│   └── __init__.py
│
├── assets/
│   └── templates/
│       └── sample_hierarchy_tree.xlsx  # Example template
│
└── test_files/                     # Comprehensive test suite
    ├── README_TEST_SUITE.md
    ├── TEST_01_perfect_tree.xlsx
    ├── TEST_02_two_root_nodes.xlsx
    └── ... (10 test files total)
```

---

## 🛣️ Roadmap

### Phase 1: Tree Converter (✅ Complete)
- [x] Visual tree parsing
- [x] Validation engine
- [x] Error detection
- [x] Duplicate handling
- [x] Vena format export

### Phase 2: Hierarchy Validator (🚧 In Progress)
- [ ] Parent-child validation
- [ ] Circular reference detection
- [ ] Orphan detection
- [ ] Depth analysis

### Phase 3: Advanced Features (📋 Planned)
- [ ] Batch processing
- [ ] API endpoints
- [ ] Custom validation rules
- [ ] Audit trail

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/hierarchy-validator.git
cd hierarchy-validator

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
streamlit run main.py

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature
```

---

## 📝 License

This project is proprietary software. All rights reserved.

---

## 💬 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Contact: [Your contact information]

---

## 🙏 Acknowledgments

Built with:
- [Streamlit](https://streamlit.io/) - Beautiful web apps in Python
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [TreeLib](https://github.com/caesar0301/treelib) - Tree data structures
- [OpenPyXL](https://openpyxl.readthedocs.io/) - Excel file handling

---

**Built with care for mid-market FP&A teams** 💚
