# Repository Organization

This document describes the organization of the IDF Creator repository.

## Directory Structure

```
idf-creator/
├── src/                    # Main source code
│   ├── core/              # Core IDF generation logic
│   ├── validation/        # Validation modules
│   ├── compliance/        # Compliance checking (ASHRAE 90.1)
│   ├── utils/             # Utility functions
│   └── ...                # Other modules
├── tests/                  # Test suite
│   ├── data/             # Test data files (JSON, etc.)
│   └── test_*.py         # Test modules
├── examples/              # Example scripts
│   ├── example.py        # Basic example
│   └── phase1_example.py # Phase 1 example
├── scripts/               # Utility scripts
│   ├── archive/          # Historical/one-off scripts
│   ├── download_weather_files.py
│   ├── calibrate_to_report.py
│   └── README.md         # Scripts documentation
├── docs/                  # Documentation
│   ├── history/         # Historical documentation (archived)
│   ├── API_DOCUMENTATION.md
│   ├── HOW_IT_WORKS.md
│   ├── TESTING_GUIDE.md
│   └── USER_WORKFLOW_GUIDE.md
├── artifacts/            # Build artifacts (gitignored)
├── test_outputs/         # Test simulation outputs (gitignored)
├── output/               # Generated IDF files (gitignored)
├── main.py               # Main entry point
├── web_interface.py      # Web interface
├── railway_config.py     # Railway deployment config
├── setup.py              # Package setup
├── requirements.txt      # Python dependencies
├── config.yaml           # Configuration file
├── README.md             # Main README
├── CONTRIBUTING.md       # Contribution guidelines
└── LICENSE               # MIT License
```

## File Organization Rules

### Source Code (`src/`)
- All production code goes here
- Organized by functionality (core, validation, compliance, etc.)
- Each module should have clear responsibilities

### Tests (`tests/`)
- All test files use `test_` prefix
- Test data files go in `tests/data/`
- Tests should be independent and runnable
- Use pytest for testing framework

### Examples (`examples/`)
- Example scripts demonstrating usage
- Should be runnable and well-documented
- Keep examples simple and focused

### Scripts (`scripts/`)
- Utility scripts for development/operations
- One-off or historical scripts go in `scripts/archive/`
- Document scripts in `scripts/README.md`

### Documentation (`docs/`)
- Current documentation in root of `docs/`
- Historical/archived docs in `docs/history/`
- Keep documentation up to date with code changes

## Ignored Files

The following are excluded from version control (see `.gitignore`):

- `artifacts/` - Build and test artifacts
- `test_outputs/` - EnergyPlus simulation outputs
- `output/` - Generated IDF files
- `__pycache__/` - Python cache files
- `*.pyc`, `*.pyo` - Compiled Python files
- `*.idf` - Generated IDF files (except examples)
- `*.epw` - Weather files
- `*.log` - Log files
- `.env` - Environment variables

## Contributing

When adding new files:

1. **Tests**: Add to `tests/` with `test_` prefix
2. **Examples**: Add to `examples/`
3. **Documentation**: Add to `docs/` (or `docs/history/` if historical)
4. **Scripts**: Add to `scripts/` (or `scripts/archive/` if one-off)
5. **Source code**: Add to appropriate subdirectory in `src/`

## Maintenance

- Keep the root directory clean - only essential files
- Move temporary/one-off scripts to `scripts/archive/`
- Archive old documentation to `docs/history/`
- Regularly clean up ignored directories locally

