# Status Tests for IDF Creator

This document describes the status testing tools available for checking the health and readiness of the IDF Creator system.

## Quick Status Check

**File**: `quick_status.py`

A simple, fast check to verify the system is ready to use. Perfect for quick health checks.

### Usage

```bash
python quick_status.py
```

### What it checks:
- Configuration file exists
- Source directory exists
- Core modules can be imported
- Key components are available
- Output directories exist
- Weather files are available (optional)

### Output
- ✅ **STATUS: READY** - All critical components available
- ⚠️ **STATUS: READY (with warnings)** - Ready but some optional items missing
- ❌ **STATUS: ISSUES FOUND** - Critical issues that need attention

---

## Comprehensive Status Check

**File**: `test_status.py`

A detailed, comprehensive status check that verifies all system components, dependencies, and configuration.

### Usage

```bash
# Full check (includes API health if server is running)
python test_status.py

# Skip API check (useful if server is not running)
python test_status.py --no-api

# Custom API URL
python test_status.py --api-url http://localhost:5001

# Save results to JSON file
python test_status.py --save

# JSON output only (for scripting/automation)
python test_status.py --json
```

### What it checks:

1. **API Status** (optional)
   - Health endpoint availability
   - Service name and version

2. **Component Imports**
   - All core modules can be imported
   - Module structure is valid

3. **Component Initialization**
   - IDFCreator can be initialized
   - Location fetchers work
   - IDF generators are ready

4. **Configuration Files**
   - config.yaml exists and is readable
   - requirements.txt exists

5. **Directory Structure**
   - Required directories exist
   - Directories are writable

6. **Python Dependencies**
   - Required packages installed
   - Optional packages status

7. **Weather Files**
   - Weather directory exists
   - EPW files are available

8. **Output Files**
   - IDF files in output directories
   - File counts and sizes

### Output Format

The comprehensive test provides:
- Color-coded status indicators
- Detailed information for each component
- Overall system status summary
- List of issues found (if any)

### Exit Codes

- `0` - System is healthy
- `1` - System is degraded (some issues but usable)
- `2` - System has critical issues

---

## Example Output

### Quick Status Example

```
🔍 Quick Status Check for IDF Creator

✓ Configuration file found
✓ Source directory found
✓ Main module can be imported
✓ IDFGenerator available
✓ LocationFetcher available
✓ Output directory exists: artifacts/desktop_files/idf
✓ 1 weather file(s) found

==================================================
✅ STATUS: READY
All critical components are available
```

### Comprehensive Status Example

The comprehensive test provides detailed sections:

```
======================================================================
                   IDF Creator System Status Check                    
======================================================================

======================================================================
                          Component Imports                           
======================================================================

✓ main.............................................. PASS
✓ idf_generator..................................... PASS
✓ professional_idf_generator........................ PASS
...

======================================================================
                        Overall Status Summary                        
======================================================================

✓ System Status: HEALTHY
All critical components are operational
```

---

## When to Use Each Test

### Use Quick Status (`quick_status.py`) when:
- You want a fast check before running the system
- You're setting up the system for the first time
- You need a simple pass/fail check
- You're writing scripts that need quick validation

### Use Comprehensive Status (`test_status.py`) when:
- You need detailed diagnostics
- You're troubleshooting issues
- You want to verify all dependencies
- You're preparing for deployment
- You need to generate status reports

---

## Integration with CI/CD

Both scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Check System Status
  run: python test_status.py --no-api --json > status.json
  
- name: Quick Health Check
  run: python quick_status.py
```

---

## Troubleshooting

### Missing Dependencies

If the status tests show missing dependencies:

```bash
pip install -r requirements.txt
```

### API Not Running

If you get API connection errors:
- Make sure the web server is running: `python web_interface.py`
- Or use `--no-api` flag to skip API checks

### Import Errors

If components fail to import:
- Check that you're in the project root directory
- Verify Python path includes the project directory
- Ensure all source files are present

---

## Status Test Results File

When using `--save` flag, results are saved to `status_check_results.json`:

```json
{
  "api": {
    "available": true,
    "status": "healthy",
    "service": "IDF Creator API",
    "version": "1.0.0"
  },
  "components": {
    "imports": {...},
    "initialization": {...}
  },
  "files": {
    "config": {...},
    "weather": {...},
    "output": {...}
  },
  "dependencies": {...},
  "directories": {...},
  "overall": {
    "status": "healthy",
    "issues": []
  }
}
```

This JSON file can be used for:
- Automated monitoring
- Status dashboards
- Logging and reporting
- Integration with monitoring tools

