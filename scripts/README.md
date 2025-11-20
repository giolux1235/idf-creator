# Scripts Directory

This directory contains utility scripts and tools for the IDF Creator project.

## Structure

- **Root scripts/**: Active utility scripts that may be useful for development or operations
- **archive/**: Historical scripts and one-off fixes that are kept for reference but not actively maintained

## Active Scripts

### `download_weather_files.py`
Downloads weather files for EnergyPlus simulations.

### `calibrate_to_report.py`
Calibration tool for matching IDF simulations to real building energy reports.

### `nlp_cli.py`
Natural language processing CLI interface for building input.

### `full_run.py`
Complete workflow script for end-to-end IDF generation and simulation.

## Archived Scripts

The `archive/` folder contains historical scripts including:
- One-off fix scripts (`fix_*.py`)
- Validation scripts (`validate_*.py`, `verify_*.py`)
- Diagnostic tools (`diagnose_*.py`, `debug_*.py`)
- Other utility scripts

These are kept for reference but are not actively maintained. If you need functionality from archived scripts, consider integrating it into the main codebase.

## Usage

Most scripts can be run directly:
```bash
python scripts/script_name.py [arguments]
```

Check individual scripts for specific usage instructions.

