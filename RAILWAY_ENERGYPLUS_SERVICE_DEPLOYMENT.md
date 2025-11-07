# Railway EnergyPlus Service - SQLite Extraction Fix Deployment

**Date**: 2025-11-05  
**Priority**: 🔴 **HIGH** - Energy extraction is incomplete  
**Service URL**: `https://web-production-1d1be.up.railway.app/simulate`

---

## 📋 **EXECUTIVE SUMMARY**

The Railway EnergyPlus service needs to be updated with SQLite extraction fixes to properly extract energy results from EnergyPlus simulations. Currently, energy values are 76% below expected because SQLite extraction is not being used.

---

## 🔧 **REQUIRED FIXES**

### Fix 1: Ensure Output:SQLite in IDF Files

**Status**: ✅ **FIXED IN IDF CREATOR** - All IDF generators now include `Output:SQLite`

The IDF Creator service (this repo) now ensures all IDF files include:
```idf
Output:SQLite,
    SimpleAndTabular;        !- Option Type
```

**Action**: ✅ **COMPLETE** - IDF Creator automatically adds this to all generated files.

---

### Fix 2: SQLite Extraction Logic

**Location**: Railway EnergyPlus Service `/simulate` endpoint

The Railway service needs to implement SQLite extraction with the following logic:

#### Current Problem

The service is using `"standard"` extraction (CSV/HTML) which provides incomplete values (76% too low).

#### Required Implementation

The service should use SQLite extraction with `MAX()` for RunPeriod meters (not `SUM()`).

**Key Points**:
- Use `MAX(Value)` for RunPeriod frequency meters (cumulative totals)
- Use `SUM(Value)` would cause 17x too high values
- SQLite extraction should be tried if CSV extraction fails or returns low values

#### Implementation Code

```python
def extract_energy_from_sqlite(sql_file_path: str) -> dict:
    """
    Extract energy results from EnergyPlus SQLite database
    
    Returns:
        dict with energy_results or None if extraction fails
    """
    import sqlite3
    import os
    
    if not os.path.exists(sql_file_path) or os.path.getsize(sql_file_path) == 0:
        return None
    
    try:
        conn = sqlite3.connect(sql_file_path)
        cursor = conn.cursor()
        
        energy_results = {}
        total_site_energy_j = 0
        
        # ELECTRICITY EXTRACTION - Use MAX() for RunPeriod (cumulative)
        electricity_queries = [
            # Strategy 1: ReportMeterDataDictionary
            """
            SELECT MAX(d.Value) 
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name LIKE '%Electricity%Facility%'
            AND m.ReportingFrequency = 'RunPeriod'
            """,
            # Strategy 2: ReportMeterDictionary (alternative schema)
            """
            SELECT MAX(d.Value) 
            FROM ReportMeterData d
            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
            WHERE m.Name LIKE '%Electricity%Facility%'
            AND m.ReportingFrequency = 'RunPeriod'
            """,
            # Strategy 3: Direct lookup
            """
            SELECT MAX(Value) 
            FROM ReportMeterData
            WHERE ReportMeterDataDictionaryIndex IN (
                SELECT ReportMeterDataDictionaryIndex
                FROM ReportMeterDataDictionary
                WHERE Name = 'Electricity:Facility'
                AND ReportingFrequency = 'RunPeriod'
            )
            """,
            # Strategy 4: Alternative table structure
            """
            SELECT MAX(Value) 
            FROM ReportMeterData
            WHERE ReportMeterDictionaryIndex IN (
                SELECT ReportMeterDictionaryIndex
                FROM ReportMeterDictionary
                WHERE Name = 'Electricity:Facility'
                AND ReportingFrequency = 'RunPeriod'
            )
            """
        ]
        
        # Try each query strategy
        for query in electricity_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    total_site_energy_j = float(result[0])
                    break
            except Exception as e:
                continue
        
        if total_site_energy_j == 0:
            conn.close()
            return None
        
        # Convert Joules to kWh (1 kWh = 3,600,000 J)
        energy_results['total_electricity_kwh'] = total_site_energy_j / 3600000.0
        energy_results['total_site_energy_kwh'] = total_site_energy_j / 3600000.0
        
        # Try to get natural gas
        gas_queries = [
            """
            SELECT MAX(d.Value) 
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name LIKE '%NaturalGas%Facility%'
            AND m.ReportingFrequency = 'RunPeriod'
            """,
            """
            SELECT MAX(d.Value) 
            FROM ReportMeterData d
            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
            WHERE m.Name LIKE '%NaturalGas%Facility%'
            AND m.ReportingFrequency = 'RunPeriod'
            """,
            """
            SELECT MAX(Value) 
            FROM ReportMeterData
            WHERE ReportMeterDataDictionaryIndex IN (
                SELECT ReportMeterDataDictionaryIndex
                FROM ReportMeterDataDictionary
                WHERE Name = 'NaturalGas:Facility'
                AND ReportingFrequency = 'RunPeriod'
            )
            """
        ]
        
        total_gas_j = 0
        for query in gas_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    total_gas_j = float(result[0])
                    break
            except:
                continue
        
        if total_gas_j > 0:
            energy_results['total_gas_kwh'] = total_gas_j / 3600000.0
            energy_results['total_site_energy_kwh'] += energy_results['total_gas_kwh']
        
        # Get building area if available
        area_queries = [
            """
            SELECT SUM(Value) 
            FROM ReportVariableData d
            JOIN ReportVariableDataDictionary v ON d.ReportVariableDataDictionaryIndex = v.ReportVariableDataDictionaryIndex
            WHERE v.Name LIKE '%Building%Area%'
            AND v.ReportingFrequency = 'RunPeriod'
            LIMIT 1
            """
        ]
        
        for query in area_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    energy_results['building_area_m2'] = float(result[0])
                    if energy_results.get('total_site_energy_kwh'):
                        energy_results['eui_kwh_m2'] = (
                            energy_results['total_site_energy_kwh'] / energy_results['building_area_m2']
                        )
                    break
            except:
                continue
        
        # Track extraction method
        energy_results['extraction_method'] = 'sqlite'
        
        conn.close()
        return energy_results
        
    except Exception as e:
        print(f"⚠️  SQLite extraction error: {e}")
        return None
```

---

### Fix 3: Extraction Method Tracking

Add `extraction_method` to API response:

```python
energy_results['extraction_method'] = 'sqlite'  # or 'standard' for CSV
```

This helps diagnose which extraction method is being used.

---

### Fix 4: Extraction Priority Logic

**Current Logic** (needs update):
- Try CSV first
- Only use SQLite if CSV fails

**Recommended Logic**:
1. Try CSV extraction first (for comprehensive end-use data)
2. If CSV returns suspiciously low values (< 20 kWh/m² EUI), try SQLite
3. Use SQLite if it provides more complete values
4. Track which method was used in response

**Example**:
```python
# After CSV extraction
if energy_results.get('total_site_energy_kwh', 0) > 0:
    building_area = energy_results.get('building_area_m2', 0)
    if building_area > 0:
        eui = energy_results['total_site_energy_kwh'] / building_area
        if eui < 15:  # Suspiciously low EUI
            # Try SQLite as fallback
            sqlite_results = extract_energy_from_sqlite(sql_file)
            if sqlite_results and sqlite_results.get('total_site_energy_kwh', 0) > energy_results['total_site_energy_kwh'] * 1.2:
                energy_results = sqlite_results
                energy_results['extraction_method'] = 'sqlite'
```

---

## 📊 **EXPECTED BEHAVIOR AFTER FIX**

### Test Case: ASHRAE Medium Office (4,645 m²)

| Metric | Before Fix | After Fix (Expected) |
|--------|-----------|---------------------|
| **EUI** | 5.19 kWh/m² ❌ | 20-28 kWh/m² ✅ |
| **Total Energy** | 24,109 kWh ❌ | 90,000-130,000 kWh ✅ |
| **Extraction Method** | `standard` ❌ | `sqlite` ✅ |
| **Accuracy** | -76.4% ❌ | ±20% ✅ |

---

## 🚀 **DEPLOYMENT STEPS**

### Step 1: Update Code

1. Add SQLite extraction function (see code above)
2. Update extraction priority logic
3. Add extraction method tracking
4. Test locally if possible

### Step 2: Deploy to Railway

1. Push code to Railway repository
2. Railway will automatically deploy
3. Wait 2-5 minutes for deployment

### Step 3: Verify Deployment

1. Test with a known building (medium office, 4,645 m²)
2. Check API response for `extraction_method: 'sqlite'`
3. Verify energy values are reasonable (~100,000 kWh)
4. Check EUI is 20-28 kWh/m²

---

## 🧪 **TESTING CHECKLIST**

After deployment, verify:

- [ ] `eplusout.sql` file exists in output directory
- [ ] SQLite extraction logs show facility meters found
- [ ] Extraction method is `"sqlite"` (not `"standard"`)
- [ ] EUI is 20-28 kWh/m² (not 5-8 kWh/m²)
- [ ] Total energy is ~100,000 kWh (not ~24,000 kWh)
- [ ] SQLite values are reasonable (not 17x too high)

---

## 📋 **API RESPONSE FORMAT**

After fixes, the API should return:

```json
{
  "version": "33.0.0",
  "simulation_status": "success",
  "energyplus_version": "25.1.0",
  "real_simulation": true,
  "energy_results": {
    "total_site_energy_kwh": 102190.0,
    "total_electricity_kwh": 85000.0,
    "total_gas_kwh": 17190.0,
    "building_area_m2": 4645.15,
    "eui_kwh_m2": 22.0,
    "extraction_method": "sqlite"
  },
  "output_files": [...],
  "processing_time": "..."
}
```

---

## 📞 **CONTACT**

If the Railway EnergyPlus service is in a separate repository:

1. **Apply the fixes** from this document
2. **Use the SQLite extraction code** provided above
3. **Test with a medium office building** (4,645 m²)
4. **Verify energy values** are ~100,000 kWh (not ~24,000 kWh)

---

## ✅ **SUMMARY**

**Status**: ⚠️ **ACTION REQUIRED** - Railway EnergyPlus service needs SQLite extraction fixes

**Next Steps**:
1. ✅ IDF Creator ensures Output:SQLite in all IDF files (COMPLETE)
2. ⏳ Railway service implements SQLite extraction (NEEDED)
3. ⏳ Railway service uses MAX() for RunPeriod meters (NEEDED)
4. ⏳ Railway service tracks extraction method (NEEDED)
5. ⏳ Test end-to-end after deployment (PENDING)

**Priority**: 🔴 **HIGH** - Energy extraction is critical for accurate EUI calculations

---

**Report Generated**: 2025-11-05  
**Contact**: EnergyPlus API Team  
**Status**: Awaiting Railway service deployment



