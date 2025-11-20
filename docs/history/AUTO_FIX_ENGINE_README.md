# Automatic IDF Fix Engine

## Overview

The Automatic IDF Fix Engine automatically:
1. **Finds weather files** on your machine
2. **Extracts location information** (city, state, address) from weather file names
3. **Generates IDF files** for each location using the IDF Creator
4. **Runs EnergyPlus simulations** to verify the IDF files
5. **Detects errors** from EnergyPlus output (.err files)
6. **Fixes errors automatically** through iterative corrections
7. **Validates energy data consistency** using CBECS benchmarks
8. **Fixes energy issues** (zero energy, unrealistic EUI, etc.)
9. **Iterates until all issues are resolved** (up to 10 iterations)

## Features

### Weather File Discovery
- Automatically searches common weather file directories:
  - `artifacts/desktop_files/weather`
  - `/usr/share/EnergyPlus/weather`
  - `/opt/EnergyPlus/weather`
  - `~/EnergyPlus/weather`
- Extracts location information from weather file names:
  - `USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw` → Chicago, IL
  - `USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw` → New York, NY
  - `USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw` → San Francisco, CA

### Automatic Error Fixing
The engine can automatically fix common EnergyPlus errors:

1. **Missing RunPeriod** - Adds RunPeriod object for year-round simulation
2. **Missing Timestep** - Adds Timestep object (6 timesteps per hour)
3. **Missing Output objects** - Adds Output:Variable and Output:Table:SummaryReports
4. **Zero area surfaces** - Removes invalid surfaces
5. **Non-planar surfaces** - Fixes geometry issues
6. **Missing thermostats** - Adds ZoneControl:Thermostat for all zones
7. **HVAC connection errors** - Fixes node connections
8. **Missing materials** - Adds standard material library

### Energy Consistency Fixing
The engine validates energy results against:
- **CBECS benchmarks** for building type
- **Absolute EUI ranges** (100-200 kWh/m²/year for offices)
- **Component energy checks** (lighting, HVAC, equipment)

And fixes:
- **Zero energy consumption** - Replaces Ideal Loads with PTAC systems
- **Low EUI** - Adds thermostats and ensures HVAC operation
- **Zero lighting energy** - Adds Lights objects
- **Zero fan energy** - Ensures fan energy reporting

## Usage

### Basic Usage

```bash
python auto_fix_all_locations.py
```

This will:
1. Find all weather files
2. Generate IDFs for each location
3. Run simulations and fix errors iteratively
4. Save results to `output/auto_fixed/`

### Output

The script generates:
- **Fixed IDF files**: `{city}_fixed.idf` in `output/auto_fixed/`
- **Simulation results**: EnergyPlus output in `output/auto_fixed/{city}/iter_{N}/`
- **Results summary**: `output/auto_fixed/results.json`

### Example Output

```
======================================================================
IDF Creator - Automatic Fix Engine
======================================================================

✓ Found EnergyPlus: /usr/local/bin/energyplus

Processing: Chicago, IL
Weather file: USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw

📍 Step 1: Generating IDF for Chicago, IL
✓ Generated IDF: output/auto_fixed/Chicago_initial.idf

🔄 Iteration 1/10
⚠️  Found 2 fatal and 5 severe errors
✓ Applied fix: Added RunPeriod; Added Timestep; Added Output objects

🔄 Iteration 2/10
⚠️  Found 0 fatal and 3 severe errors
✓ Applied fix: Removed zero-area surfaces

🔄 Iteration 3/10
✅ Success! No errors and energy data is consistent.

Final Results:
- Fatal errors: 0
- Severe errors: 0
- Warnings: 2
- Energy consistency: ✅ Valid
```

## Requirements

### EnergyPlus
The script supports two modes:

1. **Local EnergyPlus** (preferred):
   - Linux: `/usr/local/bin/energyplus` or `/opt/EnergyPlus/energyplus`
   - macOS: `/Applications/EnergyPlus-*/energyplus`
   - Windows: `C:\EnergyPlusV*\energyplus.exe`

2. **EnergyPlus API** (fallback):
   - Automatically uses API if local EnergyPlus is not found
   - API URL: `https://web-production-3092c.up.railway.app/simulate` (default)
   - Automatically tests API availability on startup
   - Can be configured via `ENERGYPLUS_API_URL` environment variable
   - The API integration is based on `test_idf_to_api.py` functionality

If neither is available, the script will still generate IDF files but skip simulations.

### Python Dependencies
All dependencies are included in `requirements.txt`:
- `shapely` - Geometry processing
- `requests` - API calls
- `pandas` - Data processing (optional, for advanced energy analysis)

## Configuration

### Custom Weather Directories

You can specify custom weather directories:

```python
from src.auto_fix_engine import AutoFixEngine

engine = AutoFixEngine(
    weather_dirs=['/path/to/weather/files', '/another/path'],
    max_iterations=15
)
```

### Maximum Iterations

Control the maximum number of fix iterations:

```python
engine = AutoFixEngine(max_iterations=20)
```

## How It Works

### 1. Weather File Discovery
```python
finder = WeatherFileFinder()
weather_files = finder.find_weather_files()
```

### 2. IDF Generation
```python
idf_creator = IDFCreator(enhanced=True, professional=True)
idf_path = idf_creator.create_idf(address="Chicago, IL", ...)
```

### 3. Simulation
```python
validator = EnergyPlusSimulationValidator()
result = validator.validate_by_simulation(idf_path, weather_file, output_dir)
```

### 4. Error Detection
```python
if result.fatal_errors > 0 or result.severe_errors > 0:
    fixer = IDFAutoFixer()
    fix_result = fixer.fix_common_errors(idf_content, error_messages)
```

### 5. Energy Validation
```python
energy_validator = EnergyCoherenceValidator()
validation = validate_energy_coherence(energy_results, building_type, area, stories)
```

### 6. Energy Fixing
```python
if validation['issues']:
    energy_fixer = EnergyConsistencyFixer()
    fix_result = energy_fixer.fix_energy_issues(idf_content, validation['issues'])
```

## Integration with EnergyPlus API

The engine automatically integrates with the EnergyPlus API (based on `test_idf_to_api.py`):

### Automatic API Fallback
- If local EnergyPlus is not found, the engine automatically tries the API
- No configuration needed - uses default Railway API URL
- API results are converted to the same format as local simulations

### Custom API URL
```python
# Set custom API URL
engine = AutoFixEngine(
    use_api=True,
    api_url='https://your-custom-api.com/simulate'
)

# Or via environment variable
export ENERGYPLUS_API_URL=https://your-custom-api.com/simulate
```

### API Features
- Sends IDF content as JSON (base64-encoded)
- Includes weather file automatically
- Handles API timeouts and connection errors gracefully
- Converts API results to format compatible with energy validation
- Saves API results for debugging

## Testing API Connection

Before running the auto-fix process, you can test your Railway API connection:

```bash
python test_api_connection.py
```

This will:
1. Test the `/health` endpoint (if available)
2. Test the `/simulate` endpoint with a minimal IDF
3. Test the `/simulate` endpoint with a weather file
4. Show a summary of API availability

The auto-fix engine automatically tests API availability on startup, but you can use this script to verify your Railway deployment is working.

## Troubleshooting

### EnergyPlus Not Found
If EnergyPlus is not found:
- Install EnergyPlus: https://energyplus.net/downloads
- Add to PATH: `export PATH=$PATH:/path/to/EnergyPlus/`
- Or specify path: `engine.energyplus_path = '/custom/path'`

### Simulation Timeouts
If simulations timeout:
- Increase timeout: `validator.validate_by_simulation(..., timeout=1200)`
- Or skip simulations and just generate IDFs

### Fixes Not Working
If fixes don't resolve issues:
- Check `output/auto_fixed/{city}/iter_{N}/eplusout.err` for detailed errors
- Review `output/auto_fixed/results.json` for fix history
- Manually review the generated IDF files

## Files Created

- `src/auto_fix_engine.py` - Main auto-fix engine module
- `auto_fix_all_locations.py` - Command-line script
- `AUTO_FIX_ENGINE_README.md` - This documentation

## Examples

### Process Single Location

```python
from src.auto_fix_engine import AutoFixEngine, WeatherFileInfo

engine = AutoFixEngine()

# Create weather info manually
weather_info = WeatherFileInfo(
    path="path/to/weather.epw",
    filename="USA_IL_Chicago.epw",
    city="Chicago",
    state="IL",
    address="Chicago, IL"
)

result = engine.process_single_location(weather_info, "output/test")
print(f"Success: {result['success']}")
```

### Custom Fix Strategies

```python
from src.auto_fix_engine import IDFAutoFixer

fixer = IDFAutoFixer()
fix_result = fixer.fix_common_errors(idf_content, error_messages)

if fix_result.success:
    fixed_idf = fix_result.idf_content
    # Apply custom fixes...
```

## Contributing

To add new fix strategies:

1. Add fix method to `IDFAutoFixer`:
```python
def _fix_new_error(self, content: str) -> str:
    # Your fix logic
    return content
```

2. Add detection in `fix_common_errors`:
```python
if 'new error' in error_text:
    fixed_content = self._fix_new_error(fixed_content)
    fixes_applied.append('Fixed new error')
```

## License

Same as the main IDF Creator project.

