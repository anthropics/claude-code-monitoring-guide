# Repository Structure

## 📁 Organized Directory Layout

```
claude-code-monitoring-guide/
├── 📋 Core Documentation
│   ├── README.md                    # Main entry point
│   ├── CLAUDE.md                    # Core workflows & commands
│   ├── docs/                        # Documentation hub
│   │   ├── INDEX.md                 # Role-based navigation
│   │   └── README.md                # Documentation guide
│   ├── JUSTFILE-GUIDE.md           # Service management
│   ├── METRICS-REFERENCE.md        # Metrics & queries
│   └── troubleshooting.md          # Diagnostic procedures
│
├── 🏗️ Infrastructure & Config
│   ├── justfile                    # Main service commands
│   ├── docker-compose.yml          # Container orchestration
│   ├── prometheus.yml              # Metrics collection
│   ├── otel-collector-config.yaml  # OTEL configuration
│   └── grafana/                    # Dashboard configuration
│       ├── dashboards/
│       └── provisioning/
│
├── 🎣 Hook System
│   ├── production-tool-hook.sh     # MAIN hook (root level)
│   └── hooks/                      # Development & specialized hooks
│       ├── debug-pretool-hook.sh   # PreToolUse debugging
│       ├── debug-stdin-hook.sh     # JSON stdin debugging
│       ├── debug-tool-hook.sh      # General hook debugging
│       ├── minimal-tool-hook.sh    # Minimal example
│       ├── tool-usage-hook.sh      # Tool usage tracking
│       ├── send-custom-metric.sh   # Custom metric sender
│       └── README.md               # Hook documentation
│
├── 🐍 Service Management
│   └── scripts/                    # Python helper scripts
│       ├── service_manager.py      # Docker orchestration
│       ├── monitor_manager.py      # Health checking
│       ├── dashboard_manager.py    # Dashboard CRUD
│       ├── test_manager.py         # Testing utilities
│       └── deploy_manager.py       # Hook deployment
│
├── 🔧 Utilities & Tools
│   └── tools/                      # Setup & utility scripts
│       ├── setup-monitoring.sh     # Legacy setup
│       ├── team-deploy.sh          # Legacy deployment
│       ├── change-ports.sh         # Port utilities
│       ├── parse-session.sh        # Session parsing
│       ├── custom-metrics-sender.py # Python metrics
│       └── README.md               # Tools documentation
│
├── ⚙️ Configuration
│   └── config/                     # Hook & system config
│       ├── hooks-config.json       # Hook configuration
│       ├── example-claude-hooks.json # Hook examples
│       └── README.md               # Config documentation
│
├── 🧪 Test Data
│   └── test-data/                  # Test files & samples
│       ├── test-compaction.txt     # Compaction test data
│       ├── test-debug.txt          # Debug scenarios
│       ├── test-hook-data.txt      # Hook JSON samples
│       ├── test-write-hook.txt     # Write hook tests
│       └── README.md               # Test data guide
│
└── 📚 Reference Materials
    ├── README-TEAM.md              # Team deployment
    ├── CUSTOM-METRICS-GUIDE.md     # Custom metrics
    ├── claude_code_roi_full.md     # Implementation details
    ├── sample-report-output.md     # Example reports
    └── report-generation-prompt.md # Report templates
```

## 🎯 Key Principles

### **Clean Root Level**
- Only essential files at root (main docs, justfile, infrastructure)
- Main production hook stays at root for easy access
- All specialized files organized into logical directories

### **Logical Grouping**
- **`hooks/`** - All hook-related development files
- **`tools/`** - Utility scripts and setup tools  
- **`config/`** - Configuration files
- **`test-data/`** - Test files and samples
- **`scripts/`** - Python service management
- **`docs/`** - Documentation hub

### **Documentation-First**
- Each directory has its own README.md
- Central navigation hub in `docs/INDEX.md`
- Role-based paths for different user types

### **Service-Oriented**
- Justfile commands hide directory complexity
- Python helpers provide advanced operations
- Clean separation between user tools and internal utilities

## 🚀 Benefits

✅ **Easy Navigation** - Find files by purpose, not by guessing  
✅ **Clear Ownership** - Each directory has a specific purpose  
✅ **Scalable** - Easy to add new tools without cluttering root  
✅ **Maintainable** - Related files grouped together  
✅ **Professional** - Follows industry best practices for repository organization

## 💡 Usage Patterns

**For daily operations** → Use justfile commands (abstracts directory structure)  
**For development** → Navigate to specific directories (hooks/, tools/, scripts/)  
**For configuration** → Check config/ directory  
**For troubleshooting** → Use test-data/ and diagnostic tools in tools/