# Code Organization: Dashboard Sections to Source Files

## Current Structure Overview

```
Dashboard Sections (4)          Source Files (6)
───────────────────            ─────────────────

📊 Low-Code Analysis    ←──┐
                           ├──→ lowcode_analysis.py (278 lines)
🤖 AI Analysis          ←──┤
                           │
💬 AI Chat              ←──┴──→ ai_analysis.py (639 lines)

🔄 Data Lineage         ←─────→ lineage_visualization.py (410 lines)

                    ┌──────────→ navigation.py (381 lines)
All sections use ───┤
                    └──────────→ config_loader.py (36 lines)

Main Coordinator ──────────────→ ode-streamlit.py (309 lines)
```

---

## Detailed File-to-Section Mapping

### 1. **ode-streamlit.py** (309 lines) - Main Coordinator
**Purpose:** Entry point and routing logic

**Contains:**
- `main()` - Page config and section routing
- `handle_lowcode_analysis()` - Routes to Low-Code section
- `handle_ai_analysis()` - Routes to AI Analysis section
- `handle_ai_chat()` - Routes to AI Chat section
- `handle_lineage_visualization()` - Routes to Data Lineage section
- `invoke_eda_method()` - Helper for EDA method dispatch

**Sections Served:** ALL (coordinator only, no UI)

---

### 2. **lowcode_analysis.py** (278 lines) - Low-Code Tools
**Purpose:** Traditional EDA methods implementation

**Contains:**
- `edaPandas()` - Basic Pandas analysis
- `edaPandasAI()` - Enhanced Pandas with AI column detection
- `edaSummaryTools()` - SummaryTools integration
- `edaDataprep()` - Dataprep EDA reports
- `edaSweetviz()` - Sweetviz reports
- `edaPygWalker()` - Interactive PyGWalker
- `edaDtale()` - Dtale integration
- `edaShowPlot()` - Display PNG plots
- Helper functions: `edaSummarizeDfColumns()`, `is_datetime_column()`
- `temp_html_file()` - Context manager for temp file cleanup

**Sections Served:** 📊 **Low-Code Analysis** ONLY

**Note:** Each EDA method is a standalone function

---

### 3. **ai_analysis.py** (639 lines) - AI-Powered Analysis
**Purpose:** AI/LLM-powered data analysis and chat

**Contains:**

#### Shared Utilities (used by both sections):
- `AIAssistant` class - Claude API integration
- `generate_summary_statistics()` - Dataset stats
- `execute_plot_code()` - Dynamic visualization execution

#### AI Analysis (EDA) Section:
- `edaAI()` - Main router for AI EDA views
- `render_data_preview_tab()` - Data preview view
- `render_statistics_tab()` - Statistics view
- `render_visualization_tab()` - Visualization builder view
- Chart renderers: `render_scatter_plot()`, `render_line_chart()`, etc.

#### AI Chat Section:
- `edaAIChat()` - Main chat interface
- `render_ai_chat_interface()` - Chat UI renderer

**Sections Served:**
- 🤖 **AI Analysis** (EDA views)
- 💬 **AI Chat** (conversational)

**Note:** Single file serves TWO sections because they share AI infrastructure

---

### 4. **lineage_visualization.py** (410 lines) - Data Lineage
**Purpose:** Pipeline lineage visualization

**Contains:**
- `visualize_graph()` - GraphML to PyVis conversion
- `edaShowLineageGraph()` - Main visualization function
- `list_graph_files()` - List available graphs
- `calculate_barycenter()` - Layout optimization (nested function)
- Constants: `LAYER_ORDER`, `LAYER_COLORS`, `NODE_STYLES`

**Sections Served:** 🔄 **Data Lineage** ONLY

**Note:** Self-contained, no dependencies on other section files

---

### 5. **navigation.py** (381 lines) - Shared Navigation
**Purpose:** Sidebar controls for all sections

**Contains:**

#### Top-Level:
- `setup_sidebar_navigation()` - Section selector (all sections use this)

#### Shared Components:
- `setup_sidebar_file_selection()` - Used by 3 sections (Low-Code, AI Analysis, AI Chat)

#### Section-Specific Sidebars:
- `setup_sidebar_lowcode()` - Low-Code Analysis sidebar
- `setup_sidebar_ai()` - AI Analysis sidebar
- `setup_sidebar_ai_chat()` - AI Chat sidebar
- `setup_sidebar_lineage()` - Data Lineage sidebar

#### Shared Utilities:
- `list_data_files()` - File listing
- `load_data_file()` - Data loading
- `read_csv()`, `read_parquet()`, `read_parquet_dataprep()` - File readers
- `display_dataset_info()` - Dataset info display

**Sections Served:** ALL (shared infrastructure)

**Note:** Each section gets its own setup function, but shares file selection logic

---

### 6. **config_loader.py** (36 lines) - Configuration
**Purpose:** Load YAML configuration

**Contains:**
- `get_dataset_groups()` - Load dataset groups from datasets.yml
- `get_data_layers()` - Load data layers from datalayers.yml

**Sections Served:** Indirectly used by Low-Code, AI Analysis, AI Chat (via navigation.py)

**Note:** Pure configuration loading, no UI

---

## Visualization: File Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    ode-streamlit.py (Main)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Imports all sections + navigation                    │  │
│  │ Routes section selection to appropriate handler      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
              │       │         │           │
    ┌─────────┘       │         │           └─────────┐
    │                 │         │                     │
    ▼                 ▼         ▼                     ▼
┌──────────┐   ┌────────────┐  ┌──────────────┐  ┌───────────┐
│ lowcode_ │   │ ai_        │  │  lineage_    │  │ navigation│
│ analysis │   │ analysis   │  │  visualiz..  │  │    .py    │
│   .py    │   │   .py      │  │    .py       │  │           │
│          │   │            │  │              │  │  (used by │
│ 📊       │   │ 🤖 + 💬    │  │  🔄          │  │  all)     │
└──────────┘   └────────────┘  └──────────────┘  └───────────┘
                                                        │
                                                        ▼
                                                   ┌────────┐
                                                   │ config │
                                                   │ _loader│
                                                   │  .py   │
                                                   └────────┘
```

---

## Section-to-File Summary

| Section | Primary File | Shared Files Used | Lines |
|---------|-------------|-------------------|-------|
| 📊 Low-Code Analysis | `lowcode_analysis.py` | `navigation.py`, `config_loader.py` | 278 |
| 🤖 AI Analysis | `ai_analysis.py` | `navigation.py`, `config_loader.py` | ~300 (half of file) |
| 💬 AI Chat | `ai_analysis.py` | `navigation.py`, `config_loader.py` | ~300 (half of file) |
| 🔄 Data Lineage | `lineage_visualization.py` | `navigation.py` | 410 |

---

## Why AI Analysis + AI Chat Share a File?

### Shared Infrastructure (saves duplication):
- `AIAssistant` class (Claude API wrapper)
- `generate_summary_statistics()` (dataset analysis)
- `execute_plot_code()` (dynamic plotting)
- Imports (anthropic, plotly, matplotlib, etc.)

### Distinction Within File:
```python
# ai_analysis.py structure:

# ━━━━ SHARED UTILITIES ━━━━
class AIAssistant:
    # Used by both sections

def generate_summary_statistics():
    # Used by both sections

def execute_plot_code():
    # Used by both sections

# ━━━━ AI ANALYSIS SECTION ━━━━
def edaAI(df, ai_view):
    # Routes to EDA views

def render_data_preview_tab():
def render_statistics_tab():
def render_visualization_tab():
    # EDA-specific views

# ━━━━ AI CHAT SECTION ━━━━
def edaAIChat(df):
    # Chat interface

def render_ai_chat_interface():
    # Chat-specific UI
```

---

## Should They Be Split?

### Current (1 file): ✅ Good
**Pros:**
- Shared AI infrastructure (no duplication)
- Related functionality (both use LLM)
- ~640 lines is still manageable
- Clear section markers in code

**Cons:**
- Not perfect 1:1 section-to-file mapping
- File serves two purposes

### Alternative (2 files): Consider if...
**When to split:**
- File grows beyond 1000 lines
- Want to add complex features to only one section
- Different team members own different sections
- Need to test sections completely independently

**How to split:**
```
ai_analysis.py (300 lines)
├── edaAI()
├── render_data_preview_tab()
├── render_statistics_tab()
└── render_visualization_tab()

ai_chat.py (300 lines)
├── edaAIChat()
└── render_ai_chat_interface()

ai_shared.py (50 lines)
├── AIAssistant class
├── generate_summary_statistics()
└── execute_plot_code()
```

---

## Recommendation: Keep Current Structure ✅

### Reasons:
1. **Logical grouping** - AI capabilities are related
2. **Avoids duplication** - Shared infrastructure stays together
3. **Manageable size** - 640 lines is reasonable
4. **Clear separation** - Well-commented sections within file
5. **Easy to split later** - If file grows, split is straightforward

### When to Reconsider:
- AI Chat grows to add multi-turn conversations, context switching, etc.
- AI Analysis adds more complex EDA features
- File exceeds ~1000 lines
- Different developers working on each section

---

## File Dependency Graph

```
ode-streamlit.py
  ├── imports: navigation
  │     └── imports: config_loader
  ├── imports: lowcode_analysis
  ├── imports: ai_analysis
  └── imports: lineage_visualization

navigation.py
  └── imports: config_loader

config_loader.py
  └── (no internal imports)

lowcode_analysis.py
  └── (no internal imports)

ai_analysis.py
  └── (no internal imports)

lineage_visualization.py
  └── (no internal imports)
```

**Note:** Clean architecture - no circular dependencies!

---

## Adding New Sections (Example)

If you add **"📓 Notebooks"** section:

### Option 1: New File (Recommended for complex sections)
```python
# notebooks.py (new file)
def edaNotebooks(multi_files):
    # Notebook interface
    pass
```

### Option 2: Extend Existing (For simple sections)
```python
# Add to existing file if closely related
# For example, if "Data Quality" is just extended statistics,
# could add to lowcode_analysis.py
```

### Decision Factors:
- **New file if:** >200 lines, independent functionality, distinct purpose
- **Extend existing if:** <100 lines, closely related, shares utilities

---

## Conclusion

### Current Structure is Good! ✅

**One-to-One Sections:**
- 📊 Low-Code → `lowcode_analysis.py`
- 🔄 Lineage → `lineage_visualization.py`

**Two-in-One (Makes Sense):**
- 🤖 AI Analysis + 💬 AI Chat → `ai_analysis.py` (share AI infrastructure)

**Shared Infrastructure:**
- All sections → `navigation.py` (sidebar controls)
- File-based sections → `config_loader.py` (configuration)

**Coordinator:**
- All sections → `ode-streamlit.py` (routing)

This structure balances:
- ✅ Separation of concerns
- ✅ Code reusability
- ✅ Maintainability
- ✅ Easy to extend

No changes needed unless files grow significantly!
