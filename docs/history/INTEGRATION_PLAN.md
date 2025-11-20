# Integration Plan: Model Calibration & Retrofit Optimization into IDF Generator

**Current Status**: These features are **separate modules** that work WITH IDF files, but are **NOT integrated** into the main IDF generation workflow.

---

## Current Architecture

### Separate Modules (Post-Processing)
- `src/model_calibration.py` - Works with **existing IDF files**
- `src/retrofit_optimizer.py` - Works with **existing IDF files**
- `main.py` - Creates IDF files, but **doesn't call** calibration/retrofit

### Current Workflow
```
User Input → IDF Generator → IDF File
                              ↓
                    (Manual step - user calls separately)
                              ↓
                    Model Calibration / Retrofit Optimization
```

---

## Proposed Integration

### Option 1: Add to `IDFCreator` Class (Recommended)

Add methods to `IDFCreator` class to enable calibration and retrofit as part of the workflow:

```python
class IDFCreator:
    def create_idf(self, ...):
        # Existing IDF generation code
        idf_path = ...
        return idf_path
    
    def create_and_calibrate_idf(self, address, utility_data, weather_file, ...):
        """Generate IDF and calibrate to utility bills"""
        # 1. Generate baseline IDF
        baseline_idf = self.create_idf(address, ...)
        
        # 2. Calibrate to utility bills
        from src.model_calibration import ModelCalibrator
        calibrator = ModelCalibrator()
        result = calibrator.calibrate_to_utility_bills(
            baseline_idf, utility_data, weather_file
        )
        return result
    
    def create_and_optimize_retrofits(self, address, utility_rates, ...):
        """Generate IDF and create retrofit scenarios"""
        # 1. Generate baseline IDF
        baseline_idf = self.create_idf(address, ...)
        
        # 2. Generate retrofit scenarios
        from src.retrofit_optimizer import RetrofitOptimizer
        optimizer = RetrofitOptimizer()
        scenarios = optimizer.generate_scenarios(...)
        optimized = optimizer.optimize(scenarios, utility_rates, ...)
        return optimized
```

### Option 2: Add CLI Arguments

Add command-line flags to `main.py`:

```python
parser.add_argument('--calibrate', action='store_true',
                    help='Calibrate IDF to utility bills after generation')
parser.add_argument('--utility-data', type=str,
                    help='Path to utility bill data JSON file')
parser.add_argument('--generate-retrofits', action='store_true',
                    help='Generate retrofit scenarios after IDF creation')
parser.add_argument('--utility-rates', type=str,
                    help='Path to utility rates JSON file')
```

### Option 3: Add to API Endpoints

If there's a web API, add endpoints:
- `POST /api/idf/calibrate` - Generate and calibrate IDF
- `POST /api/idf/retrofits` - Generate IDF and retrofit scenarios

---

## Recommended Implementation

**Integrate into `IDFCreator` class** with optional flags:

```python
def create_idf(self, address, ..., 
               calibrate_to_utility_bills=None,
               generate_retrofit_scenarios=False,
               utility_rates=None):
    """
    Create IDF file with optional calibration and retrofit generation.
    
    Args:
        calibrate_to_utility_bills: UtilityData object for calibration
        generate_retrofit_scenarios: If True, generate retrofit scenarios
        utility_rates: UtilityRates object for retrofit analysis
    """
    # Generate IDF
    idf_path = self._generate_idf(...)
    
    # Optional calibration
    if calibrate_to_utility_bills:
        idf_path = self._calibrate_idf(idf_path, calibrate_to_utility_bills)
    
    # Optional retrofit scenarios
    if generate_retrofit_scenarios:
        scenarios = self._generate_retrofit_scenarios(idf_path, utility_rates)
        return {'idf_path': idf_path, 'retrofit_scenarios': scenarios}
    
    return idf_path
```

---

## Benefits of Integration

1. **Seamless Workflow**: One command generates IDF + calibrates + optimizes
2. **Better UX**: Users don't need to manually chain operations
3. **LEED Ready**: Complete workflow for LEED documentation
4. **Competitive**: Matches engineer workflow (generate → calibrate → optimize)

---

## Implementation Steps

1. Add import statements to `main.py`
2. Add helper methods to `IDFCreator` class
3. Add CLI arguments for calibration/retrofit
4. Update documentation
5. Add integration tests

---

**Status**: ⚠️ **Not Yet Integrated** - Features exist but are separate modules





