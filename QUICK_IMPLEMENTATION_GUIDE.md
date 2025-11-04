# Quick Implementation Guide - SQLite Extraction

## TL;DR - What to Add

Add this function to your external EnergyPlus API and call it when SQLite file exists:

```python
def extract_energy_from_sqlite(sql_file_path):
    """Extract energy from EnergyPlus SQLite database"""
    import sqlite3
    
    if not os.path.exists(sql_file_path) or os.path.getsize(sql_file_path) == 0:
        return None
    
    try:
        conn = sqlite3.connect(sql_file_path)
        cursor = conn.cursor()
        
        # Try to get electricity (try multiple query formats)
        electricity_queries = [
            # Try ReportMeterDataDictionary first
            "SELECT SUM(d.Value) FROM ReportMeterData d JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex WHERE m.Name LIKE '%Electricity%Facility%' AND m.ReportingFrequency = 'RunPeriod'",
            # Try ReportMeterDictionary
            "SELECT SUM(d.Value) FROM ReportMeterData d JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex WHERE m.Name LIKE '%Electricity%Facility%' AND m.ReportingFrequency = 'RunPeriod'",
            # Direct lookup
            "SELECT SUM(Value) FROM ReportMeterData WHERE ReportMeterDataDictionaryIndex IN (SELECT ReportMeterDataDictionaryIndex FROM ReportMeterDataDictionary WHERE Name = 'Electricity:Facility' AND ReportingFrequency = 'RunPeriod')"
        ]
        
        total_joules = 0
        for query in electricity_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    total_joules = float(result[0])
                    break
            except:
                continue
        
        if total_joules == 0:
            conn.close()
            return None
        
        # Convert Joules to kWh (1 kWh = 3,600,000 J)
        energy_results = {
            'total_site_energy_kwh': total_joules / 3600000.0,
            'total_electricity_kwh': total_joules / 3600000.0
        }
        
        # Try to get gas
        gas_queries = [
            "SELECT SUM(d.Value) FROM ReportMeterData d JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex WHERE m.Name LIKE '%NaturalGas%Facility%' AND m.ReportingFrequency = 'RunPeriod'",
            "SELECT SUM(d.Value) FROM ReportMeterData d JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex WHERE m.Name LIKE '%NaturalGas%Facility%' AND m.ReportingFrequency = 'RunPeriod'"
        ]
        
        for query in gas_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    gas_joules = float(result[0])
                    energy_results['total_gas_kwh'] = gas_joules / 3600000.0
                    energy_results['total_site_energy_kwh'] += energy_results['total_gas_kwh']
                    break
            except:
                continue
        
        # Try to get building area
        area_queries = [
            "SELECT SUM(Value) FROM ReportVariableData d JOIN ReportVariableDataDictionary v ON d.ReportVariableDataDictionaryIndex = v.ReportVariableDataDictionaryIndex WHERE v.Name LIKE '%Floor Area%' AND v.ReportingFrequency = 'RunPeriod' LIMIT 1",
            "SELECT SUM(Value) FROM ReportVariableData d JOIN ReportVariableDictionary v ON d.ReportVariableDictionaryIndex = v.ReportVariableDictionaryIndex WHERE v.Name LIKE '%Floor Area%' AND v.ReportingFrequency = 'RunPeriod' LIMIT 1"
        ]
        
        for query in area_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    area = float(result[0])
                    if area > 0:
                        energy_results['building_area_m2'] = area
                        energy_results['eui_kwh_m2'] = energy_results['total_site_energy_kwh'] / area
                        break
            except:
                continue
        
        conn.close()
        return energy_results
        
    except Exception as e:
        return None
```

## Where to Add It

In your `/simulate` endpoint, after EnergyPlus runs:

```python
# After simulation completes
sql_file = os.path.join(output_dir, 'eplusout.sql')

# Try CSV first (if exists)
energy_results = extract_from_csv(csv_file) if os.path.exists(csv_file) else None

# If no CSV, try SQLite
if not energy_results and os.path.exists(sql_file):
    energy_results = extract_energy_from_sqlite(sql_file)

# Return response
if energy_results:
    return jsonify({
        'simulation_status': 'success',  # ✅ Change to success!
        'energy_results': energy_results,  # ✅ Add this!
        # ... other fields
    }), 200
```

## Key Points

1. **Values are in Joules** - Divide by 3,600,000 to get kWh
2. **Try multiple query formats** - Different EnergyPlus versions use different schemas
3. **Return success when results found** - Change status from "error" to "success"
4. **Include energy_results field** - This is what the client expects

## Expected Result

```json
{
  "simulation_status": "success",
  "energy_results": {
    "total_site_energy_kwh": 12345.67,
    "total_electricity_kwh": 10000.00,
    "building_area_m2": 4645.15,
    "eui_kwh_m2": 2.66
  }
}
```

## Full Documentation

See `EXTERNAL_API_SQLITE_EXTRACTION_SPEC.md` for complete details with all query strategies and error handling.



