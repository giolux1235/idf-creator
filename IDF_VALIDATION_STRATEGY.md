# IDF Validation & Quality Assurance Strategy

## 🎯 Validation Approaches

Multiple ways to check if your generated IDFs are accurate:

---

## 1. **BESTEST Validation** (Industry Standard)

### What is BESTEST?
Building Energy Simulation Test suite from NREL/ASHRAE Standard 140

### How to use it:
```bash
# Use the BESTEST-GSR repository we found earlier
git clone https://github.com/NREL/BESTEST-GSR
cd BESTEST-GSR

# Run your IDF against BESTEST test cases
openstudio run -w test_case/datapoint.osw
```

### What it checks:
- ✅ Heating/cooling load calculations
- ✅ Envelope heat transfer
- ✅ ASHRAE Standard 140 compliance
- ✅ Comparability with other tools

### Pros:
- Industry standard
- Comprehensive
- Validates physics correctness

### Cons:
- Setup required
- Requires OpenStudio
- Time-consuming

---

## 2. **EnergyPlus File Checker** (Syntax Validation)

### Built-in validation:
```bash
# EnergyPlus has built-in validation
energyplus --readvars --idd /path/to/Energy+.idd your_file.idf

# Check output for errors
cat your_file.err
```

### What it checks:
- ✅ Syntax errors
- ✅ Object references
- ✅ Field value ranges
- ✅ Required fields present

### Python check:
```python
# In your IDF Creator
from pyenergyplus.api import EnergyPlusAPI

def validate_idf_syntax(idf_file):
    api = EnergyPlusAPI()
    # Run pre-processing
    state = api.state_manager.new_state()
    api.runtime.run_energyplus(state, ["--ddy-only", "-w", "weather.epw", "-i", idf_file])
    # Check error file
    errors = read_error_file()
    return len(errors) == 0
```

---

## 3. **IDF Comparison with Model America** (Reference Dataset)

### Cross-reference approach:
```python
# Compare your IDF to Model America buildings
from src.model_america_validator import ModelAmericaValidator

validator = ModelAmericaValidator()

# Load similar building from Model America
reference = validator.get_building(
    lat=40.748, 
    lon=-73.986, 
    building_type='Office'
)

# Compare parameters
comparison = validator.compare(
    your_idf_params,
    reference_params
)

# Check if within tolerances
if comparison['within_tolerance']:
    print("✅ IDF parameters match industry dataset")
```

### What to compare:
- Building footprint area
- Window-to-wall ratio
- Number of stories
- Building type
- Climate zone

### Tolerance ranges:
```python
TOLERANCES = {
    'area': 0.10,        # ±10%
    'height': 0.05,      # ±5%
    'stories': 0,        # Exact
    'wwr': 0.05,         # ±5%
}
```

---

## 4. **Statistical Validation** (Sanity Checks)

### Parameter ranges check:
```python
def validate_parameters(params):
    """Check if parameters are within reasonable ranges."""
    checks = {
        'stories': (1, 200),
        'floor_area': (10, 500000),  # m²
        'wwr': (0, 0.8),
        'people_per_m2': (0.001, 1.0),
        'lighting_w_per_m2': (1, 50),
    }
    
    errors = []
    for param, (min_val, max_val) in checks.items():
        value = params.get(param)
        if value < min_val or value > max_val:
            errors.append(f"{param}: {value} out of range [{min_val}, {max_val}]")
    
    return len(errors) == 0, errors
```

### Building physics checks:
```python
def validate_building_physics(idf_data):
    """Check physical consistency."""
    checks = []
    
    # Zone volume must match area × height
    zone_volume = idf_data['zone_area'] * idf_data['ceiling_height']
    if abs(zone_volume - idf_data['zone_volume']) > 1:
        checks.append("Volume doesn't match area × height")
    
    # People count should match area
    expected_people = idf_data['zone_area'] * idf_data['people_per_m2']
    if abs(expected_people - idf_data['people']) > 5:
        checks.append("People count seems off")
    
    # Lighting power should match area
    expected_lighting = idf_data['zone_area'] * idf_data['lighting_w_per_m2']
    if abs(expected_lighting - idf_data['lighting_power']) > 100:
        checks.append("Lighting power seems off")
    
    return len(checks) == 0, checks
```

---

## 5. **Visualization Validation** (Geometry Check)

### Generate 3D view:
```python
# Use EnergyPlus Radiance output
energyplus -r your_file.idf  # Generate Radiance files

# Or use OpenStudio
openstudio -m your_file.idf  # Open in OpenStudio GUI
```

### What to check visually:
- ✅ Building shape looks correct
- ✅ Windows on facades make sense
- ✅ Multiple stories are present
- ✅ Dimensions seem reasonable

### Automated geometry check:
```python
def validate_geometry(idf_data):
    """Check geometric consistency."""
    # All surfaces should form closed volumes
    # Windows should be within wall boundaries
    # No overlapping surfaces
    pass
```

---

## 6. **Runtime Validation** (Simulation Test)

### Quick test simulation:
```bash
# Run short simulation
energyplus -w weather.epw your_file.idf

# Check outputs
# - No fatal errors
# - Reasonable energy use
# - Convergence achieved
```

### Automated check:
```python
def validate_simulation(idf_file):
    """Run simulation and check for errors."""
    result = run_energyplus(idf_file)
    
    checks = {
        'no_fatal_errors': check_error_file('FATAL', count=0),
        'reasonably_converged': check_convergence(),
        'energy_use_sensible': validate_energy_use(),
    }
    
    return all(checks.values()), checks
```

### Reasonable bounds check:
```python
# Energy use should be reasonable
ENERGY_USE_BOUNDS = {
    'Office': (10, 200),        # kWh/m²/year
    'Residential': (30, 150),
    'Retail': (50, 300),
    'Warehouse': (20, 100),
}

def validate_energy_use(annual_kwh, area, building_type):
    kwh_per_m2 = annual_kwh / area
    bounds = ENERGY_USE_BOUNDS.get(building_type)
    if bounds:
        min_val, max_val = bounds
        return min_val <= kwh_per_m2 <= max_val
    return True
```

---

## 7. **Cross-Reference with Google Maps** (External Validation)

### Compare with satellite imagery:
```python
from src.map_validator import MapValidator

validator = MapValidator()
building_data = validator.get_google_maps_data(address)

comparison = {
    'footprint_match': compare_footprints(
        idf_footprint, 
        google_footprint
    ),
    'height_match': abs(idf_height - google_height) < 3,
    'type_match': idf_type == google_building_type
}
```

---

## 📋 Recommended Validation Workflow

### Level 1: Syntax Check (Fast)
```bash
energyplus --readvars -i your_file.idf
```
- ✅ Basic file integrity
- ✅ Valid IDF syntax
- ⏱️ ~1 second

### Level 2: Parameter Validation (Fast)
```python
validate_parameters(building_params)
validate_building_physics(idf_data)
```
- ✅ Parameter ranges
- ✅ Physical consistency
- ⏱️ ~1 second

### Level 3: Comparison Check (Medium)
```python
compare_with_model_america(idf_params)
compare_with_osm(data)
```
- ✅ Industry consistency
- ✅ External data match
- ⏱️ 5–10 seconds

### Level 4: Level 4: Simulation Test (Slow)
```bash
energyplus -w weather.epw your_file.idf
```
- ✅ Simulation runs successfully
- ✅ No fatal errors
- ✅ Reasonable results
- ⏱️ Several minutes

### Level 5: BESTEST Validation (Very Slow)
```bash
run_bestest_tests(idf_file)
```
- ✅ Industry standard compliance
- ✅ Physics correctness
- ⏱️ Hours

---

## 🛠️ Implementation in IDF Creator

### Add validation module:
```python
# src/idf_validator.py

class IDFValidator:
    def __init__(self):
        self.checks = []
    
    def validate_complete(self, idf_file, building_params):
        """Run all validation checks."""
        results = {
            'syntax': self.check_syntax(idf_file),
            'parameters': self.check_parameters(building_params),
            'physics': self.check_physics(building_params),
            'comparison': self.check_model_america(building_params),
            'simulation': self.check_simulation(idf_file)  # Optional
        }
        
        return results
    
    def generate_report(self, results):
        """Generate human-readable report."""
        report = "IDF Validation Report\n"
        report += "=" * 50 + "\n\n"
        
        for check_name, (passed, details) in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            report += f"{check_name}: {status}\n"
            if details:
                report += f"  {details}\n"
        
        return report
```

### Add to main workflow:
```python
# In main.py

creator.create_idf(...)
validator = IDFValidator()
results = validator.validate_complete(idf_file, building_params)
validator.generate_report(results)
```

---

## 📊 Validation Metrics

### Quality Score:
```python
def calculate_quality_score(results):
    """Calculate overall quality score (0-100)."""
    weights = {
        'syntax': 0.20,      # Must be correct
        'parameters': 0.20,   # Should be reasonable
        'physics': 0.20,      # Physics must be sound
        'comparison': 0.20,   # Should match references
        'simulation': 0.20,   # Should run successfully
    }
    
    score = 0
    for check, weight in weights.items():
        if results[check][0]:  # If passed
            score += weight * 100
    
    return score
```

---

## 🎯 Recommendation

**Start with Levels 1-3 (Fast validation):**
- Syntax check
- Parameter validation
- Comparison with external data

**Add Levels 4-5 when needed:**
- For critical projects
- Before publishing IDFs
- For quality assurance

**Priority:**
1. ✅ Syntax validation (critical)
2. ✅ Parameter ranges (high)
3. ⭐ Comparison checks (medium)
4. ⭐ Simulation test (low)
5. ⭐ BESTEST (very low)

This gives you confidence in 99% of cases without running full simulations every time.







