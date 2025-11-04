# Testing Guide for IDF Creator

**Status**: ✅ Local Testing Ready | ⚠️ CI/CD Setup Optional

---

## Quick Answer

**You can test everything locally first** - no need to push to git! All tests are designed to work locally.

---

## Testing Strategy

### 1. ✅ Local Testing (Recommended First)

Test everything locally before pushing to git:

```bash
# Run all validation tests
python tests/regression_test_suite.py

# Run specific test suites
python tests/test_validation.py
python tests/test_physics.py
python tests/test_bestest.py
python tests/test_simulation.py

# Run comprehensive validation
python tests/test_comprehensive_validation.py

# Test Empire State Building simulation
python test_empire_state_simulation.py
```

### 2. ⚠️ CI/CD Testing (Optional)

Set up CI/CD for automated testing on every git push (recommended for production).

---

## Local Testing Setup

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: Install EnergyPlus for simulation tests
# (Tests handle missing EnergyPlus gracefully)
```

### Test Suites Available

#### 1. **Basic Validation Tests**
```bash
python tests/test_validation.py
```
**What it tests**:
- IDF syntax validation
- Required objects check
- Schedule references
- HVAC topology validation

#### 2. **Physics Consistency Tests**
```bash
python tests/test_physics.py
```
**What it tests**:
- Zone closure validation
- Surface adjacencies
- Material property ranges
- Load balance checks
- Volume consistency

#### 3. **BESTEST Compliance Tests**
```bash
python tests/test_bestest.py
```
**What it tests**:
- BESTEST criteria compliance
- Required objects
- Material properties
- Infiltration rates
- Compliance score calculation

#### 4. **Simulation Tests**
```bash
python tests/test_simulation.py
```
**What it tests**:
- EnergyPlus error parsing
- Simulation execution (if EnergyPlus available)
- Result extraction

#### 5. **Comprehensive Integration Tests**
```bash
python tests/test_comprehensive_validation.py
```
**What it tests**:
- End-to-end workflow
- All validation types combined
- Real building generation

#### 6. **Regression Test Suite**
```bash
python tests/regression_test_suite.py
```
**What it tests**:
- All building types (Office, Retail, School, Hospital, Residential, Warehouse)
- All HVAC types (VAV, PTAC, RTU)
- Edge cases (small/large buildings, single story)

#### 7. **Empire State Building End-to-End Test**
```bash
python test_empire_state_simulation.py
```
**What it tests**:
- Real-world address processing
- Complete IDF generation
- EnergyPlus simulation execution
- Result extraction

---

## Running All Tests

### Option 1: Run All Tests with pytest

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_validation.py -v

# Run specific test function
pytest tests/test_validation.py::test_valid_idf -v
```

### Option 2: Run Individual Test Scripts

```bash
# All tests are standalone scripts
python tests/regression_test_suite.py
python tests/test_validation.py
python tests/test_physics.py
python tests/test_bestest.py
python tests/test_simulation.py
python tests/test_comprehensive_validation.py
```

### Option 3: Quick Test (Recommended for Development)

```bash
# Quick validation test (no simulation)
python tests/regression_test_suite.py

# Full test with simulation (requires EnergyPlus)
python test_empire_state_simulation.py
```

---

## What Gets Tested Locally

### ✅ Always Tested (No External Dependencies)

1. **IDF Generation**
   - ✅ All building types
   - ✅ All HVAC systems
   - ✅ Geometry generation
   - ✅ Material library
   - ✅ Schedules generation

2. **Syntax Validation**
   - ✅ Required objects
   - ✅ Field structure
   - ✅ Schedule references
   - ✅ HVAC topology

3. **Physics Validation**
   - ✅ Zone closure
   - ✅ Material properties
   - ✅ Load balance
   - ✅ Volume consistency

4. **BESTEST Compliance**
   - ✅ Required objects check
   - ✅ Material ranges
   - ✅ Compliance scoring

### ⚠️ Conditionally Tested (Requires EnergyPlus)

1. **EnergyPlus Simulation**
   - ⚠️ Requires EnergyPlus installed
   - ⚠️ Requires weather files (optional)
   - ✅ Tests handle missing EnergyPlus gracefully

---

## Fixing Test Failures

### Common Issues

#### 1. Import Errors
```bash
# Make sure you're in the project root
cd "/Users/giovanniamenta/IDF - CREATOR"

# Install dependencies
pip install -r requirements.txt
```

#### 2. Missing EnergyPlus
```bash
# Tests work without EnergyPlus, but simulation tests will skip
# To install EnergyPlus:
# macOS: brew install energyplus
# Or download from https://energyplus.net/downloads
```

#### 3. Missing Weather Files
```bash
# Simulation tests work without weather files
# They'll show clear errors if weather file is missing
# Download from: https://energyplus.net/weather
```

#### 4. Validation Error Bug
If you see `TypeError: 'NoneType' object does not support item assignment`:
- This is a bug in `validate_idf_file()` - fix it first
- Or use `validator.validate()` directly

---

## Setting Up CI/CD (Optional)

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run validation tests
      run: |
        python tests/regression_test_suite.py
        pytest tests/test_validation.py tests/test_physics.py tests/test_bestest.py -v
    
    - name: Run simulation tests (skip if EnergyPlus not available)
      continue-on-error: true
      run: |
        pytest tests/test_simulation.py -v
```

### Railway CI/CD

Railway automatically runs on git push:
1. Push to GitHub
2. Railway detects changes
3. Runs deployment
4. Can add test step in `railway.json`

---

## Recommended Workflow

### For Development

1. **Make changes locally**
2. **Run quick tests**:
   ```bash
   python tests/regression_test_suite.py
   ```
3. **Test specific feature**:
   ```bash
   python tests/test_validation.py
   ```
4. **Test full workflow**:
   ```bash
   python test_empire_state_simulation.py
   ```
5. **Fix any failures**
6. **Push to git** (tests pass locally)

### For Production

1. **Run all tests locally first**
2. **Push to git**
3. **CI/CD runs tests automatically** (if configured)
4. **Deploy if tests pass**

---

## Test Results Interpretation

### ✅ Success Indicators

```
✓ ALL TESTS PASSED!
Total Tests: 10
Passed: 10 (100.0%)
Failed: 0
```

### ⚠️ Warning Indicators

```
⚠ Simulation validation skipped (EnergyPlus may not be available)
⚠ Weather file not found locally
```

These are **expected** and don't indicate failure.

### ❌ Failure Indicators

```
✗ TEST FAILED
✗ Simulation had errors
  - 1 fatal error(s)
```

These need to be fixed before pushing.

---

## Current Test Status

### Passing Tests ✅
- ✅ Regression test suite: 10/10 (100%)
- ✅ Physics validation: Working
- ✅ BESTEST validation: Working
- ✅ Simulation framework: Working
- ✅ Error parsing: Working

### Known Issues ⚠️
- ⚠️ Some validation tests fail due to `validate_idf_file()` return bug
- ⚠️ Simulation requires weather files (expected)
- ⚠️ EnergyPlus optional (tests handle gracefully)

---

## Quick Test Commands

```bash
# Test everything locally (recommended)
python tests/regression_test_suite.py && \
python tests/test_comprehensive_validation.py

# Test with pytest
pytest tests/ -v --tb=short

# Test Empire State Building
python test_empire_state_simulation.py

# Test specific component
python -c "from src.validation import validate_idf_file; print('OK')"
```

---

## Next Steps

1. ✅ **Test locally first** - All tests work without git
2. ⚠️ **Fix any failures** - See "Fixing Test Failures" section
3. ✅ **Push to git** - Once tests pass locally
4. ⚠️ **Set up CI/CD** - Optional, for automated testing

---

## Summary

**You can test everything locally** - no git push needed! 

- ✅ All test suites run locally
- ✅ No external dependencies required (except EnergyPlus for simulation)
- ✅ Tests handle missing components gracefully
- ✅ Push to git only after local tests pass

**Recommended**: Run `python tests/regression_test_suite.py` before pushing.






