# File Cleanup Plan

## Files to Keep (Essential)

### Core Application
- main.py
- web_interface.py
- nlp_cli.py
- example.py

### Configuration
- config.yaml
- requirements.txt
- setup.py
- runtime.txt
- Procfile
- railway_config.py
- railway_setup.sh
- railway.json

### Documentation (Essential)
- README.md
- START_HERE.md
- API_DOCUMENTATION.md
- PROJECT_SUMMARY.md
- HOW_IT_WORKS.md
- REFACTORING_SUMMARY.md
- LICENSE

### Source Code
- src/ (entire directory - all source modules)

### Tests (Organized)
- tests/ (entire directory - organized tests)

## Files to Remove

### Redundant Status/Result Markdown Files
- All *_COMPLETE.md files (one-time status reports)
- All *_RESULTS.md files (old test results)
- All *_ANALYSIS.md files (old analysis)
- All *_STATUS.md files (old status reports)
- All *_PROGRESS.md files (old progress reports)
- All *_ROADMAP.md files (old roadmaps - except essential ones)

### Obsolete Test Files (Root Level)
- test_*.py (move to tests/ if needed, otherwise remove)
- quick_final_test.py
- final_test.py
- benchmark_with_known_buildings.py
- analyze_chicago_austin_results.py
- extract_energy_from_sql.py
- check_hvac_and_energy.py
- test_*.py files in root

### One-Time Analysis Scripts
- senior_engineer_audit.py (one-time audit)

### Archive Folder (if redundant)
- docs_archive/ (review and keep only essential archived docs)

