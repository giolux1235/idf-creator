#!/usr/bin/env python3
"""
Diagnostic script to test SQLite extraction and verify it works correctly.
This script:
1. Generates an IDF file
2. Runs a simulation (or uses existing output)
3. Tests SQLite extraction
4. Reports extraction method used
"""

import sys
import os
from pathlib import Path
import sqlite3
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_sqlite_extraction(sqlite_path: str) -> dict:
    """Test SQLite extraction using the same logic as web_interface.py"""
    results = {
        'file_exists': os.path.exists(sqlite_path),
        'file_size': 0,
        'tables': [],
        'electricity_found': False,
        'gas_found': False,
        'extraction_method': None,
        'energy_values': {},
        'errors': []
    }
    
    if not results['file_exists']:
        results['errors'].append(f"SQLite file not found: {sqlite_path}")
        return results
    
    results['file_size'] = os.path.getsize(sqlite_path)
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        results['tables'] = [row[0] for row in cursor.fetchall()]
        
        # Check for ReportMeterDataDictionary or ReportMeterDictionary
        has_meter_dict = 'ReportMeterDataDictionary' in results['tables'] or 'ReportMeterDictionary' in results['tables']
        has_meter_data = 'ReportMeterData' in results['tables']
        
        if not has_meter_dict or not has_meter_data:
            results['errors'].append(f"Required tables missing. Has meter dict: {has_meter_dict}, Has meter data: {has_meter_data}")
            conn.close()
            return results
        
        # Try electricity extraction (using MAX() for RunPeriod)
        electricity_queries = [
            # Strategy 1: ReportMeterDataDictionary
            """
            SELECT MAX(d.Value) 
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name LIKE '%Electricity%Facility%'
            AND m.ReportingFrequency = 'RunPeriod'
            """,
            # Strategy 2: ReportMeterDictionary
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
        
        total_electricity_j = 0
        used_query = None
        for query in electricity_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                if result and result[0] and result[0] > 0:
                    total_electricity_j = float(result[0])
                    used_query = query.strip()[:50] + "..."
                    results['electricity_found'] = True
                    break
            except Exception as e:
                results['errors'].append(f"Electricity query failed: {str(e)[:100]}")
                continue
        
        if results['electricity_found']:
            results['energy_values']['electricity_kwh'] = total_electricity_j / 3600000.0
            results['energy_values']['electricity_j'] = total_electricity_j
            results['query_used'] = used_query
        
        # Try natural gas extraction
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
                    results['gas_found'] = True
                    break
            except Exception as e:
                continue
        
        if results['gas_found']:
            results['energy_values']['gas_kwh'] = total_gas_j / 3600000.0
            results['energy_values']['gas_j'] = total_gas_j
        
        # Calculate total site energy
        if results['electricity_found']:
            total_site_energy_kwh = results['energy_values'].get('electricity_kwh', 0)
            if results['gas_found']:
                total_site_energy_kwh += results['energy_values'].get('gas_kwh', 0)
            results['energy_values']['total_site_energy_kwh'] = total_site_energy_kwh
            results['extraction_method'] = 'sqlite'
        
        # Check for RunPeriod meter data
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name = 'Electricity:Facility'
            AND m.ReportingFrequency = 'RunPeriod'
        """)
        row_count = cursor.fetchone()[0]
        results['row_count'] = row_count
        
        if row_count > 1:
            results['errors'].append(f"⚠️  WARNING: {row_count} rows found for RunPeriod meter (should be 1). Using MAX() is correct.")
        
        conn.close()
        
    except Exception as e:
        results['errors'].append(f"SQLite connection error: {str(e)}")
    
    return results

def check_idf_for_sqlite(idf_path: str) -> dict:
    """Check if IDF file contains Output:SQLite"""
    results = {
        'idf_exists': os.path.exists(idf_path),
        'has_output_sqlite': False,
        'sqlite_option': None,
        'has_meters': False,
        'meter_names': []
    }
    
    if not results['idf_exists']:
        return results
    
    try:
        with open(idf_path, 'r') as f:
            content = f.read()
        
        # Check for Output:SQLite
        if 'Output:SQLite' in content:
            results['has_output_sqlite'] = True
            # Try to extract option type
            import re
            match = re.search(r'Output:SQLite,\s*([^;]+);', content)
            if match:
                results['sqlite_option'] = match.group(1).strip()
        
        # Check for meters
        if 'Output:Meter,' in content:
            results['has_meters'] = True
            # Extract meter names
            matches = re.findall(r'Output:Meter,\s*([^,]+),', content)
            results['meter_names'] = [m.strip() for m in matches]
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def main():
    """Main diagnostic function"""
    print("=" * 80)
    print("SQLITE EXTRACTION DIAGNOSTIC")
    print("=" * 80)
    
    # Check if SQLite file path provided
    if len(sys.argv) > 1:
        sqlite_path = sys.argv[1]
    else:
        # Try to find a SQLite file in common output directories
        possible_paths = [
            'test_outputs/sim_*/eplusout.sql',
            'output/*/eplusout.sql',
            'artifacts/desktop_files/simulations/*/eplusout.sql',
        ]
        
        sqlite_path = None
        for pattern in possible_paths:
            matches = list(Path('.').glob(pattern))
            if matches:
                sqlite_path = str(matches[0])
                break
        
        if not sqlite_path:
            print("\n❌ No SQLite file found. Usage:")
            print("   python test_sqlite_extraction_diagnostic.py <path_to_eplusout.sql>")
            print("\nOr provide an IDF file to check:")
            print("   python test_sqlite_extraction_diagnostic.py --idf <path_to_file.idf>")
            return
    
    # Check if it's an IDF file check
    if '--idf' in sys.argv or sqlite_path.endswith('.idf'):
        if sqlite_path.endswith('.idf'):
            idf_path = sqlite_path
        else:
            idx = sys.argv.index('--idf')
            idf_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else sqlite_path
        
        print(f"\n1. CHECKING IDF FILE: {idf_path}")
        print("-" * 80)
        idf_check = check_idf_for_sqlite(idf_path)
        
        if idf_check['has_output_sqlite']:
            print(f"✅ Output:SQLite found")
            print(f"   Option: {idf_check['sqlite_option']}")
        else:
            print(f"❌ Output:SQLite NOT found in IDF file")
            print(f"   ⚠️  This will prevent SQLite file generation!")
        
        if idf_check['has_meters']:
            print(f"✅ Meters found: {', '.join(idf_check['meter_names'])}")
        else:
            print(f"❌ No Output:Meter objects found")
        
        return
    
    # Test SQLite extraction
    print(f"\n1. TESTING SQLITE EXTRACTION: {sqlite_path}")
    print("-" * 80)
    
    extraction_results = test_sqlite_extraction(sqlite_path)
    
    if extraction_results['file_exists']:
        print(f"✅ SQLite file found ({extraction_results['file_size']:,} bytes)")
        print(f"   Tables: {', '.join(extraction_results['tables'][:10])}")
        
        if extraction_results['electricity_found']:
            print(f"\n✅ Electricity extraction successful")
            print(f"   Value: {extraction_results['energy_values']['electricity_kwh']:,.2f} kWh")
            print(f"   Raw value: {extraction_results['energy_values']['electricity_j']:,.0f} J")
            print(f"   Query used: {extraction_results.get('query_used', 'N/A')}")
        else:
            print(f"\n❌ Electricity extraction failed")
            print(f"   Errors: {extraction_results['errors']}")
        
        if extraction_results['gas_found']:
            print(f"\n✅ Natural Gas extraction successful")
            print(f"   Value: {extraction_results['energy_values']['gas_kwh']:,.2f} kWh")
        else:
            print(f"\n⚠️  Natural Gas not found (may be zero or not present)")
        
        if extraction_results['extraction_method']:
            print(f"\n✅ Extraction method: {extraction_results['extraction_method']}")
            if 'total_site_energy_kwh' in extraction_results['energy_values']:
                print(f"   Total Site Energy: {extraction_results['energy_values']['total_site_energy_kwh']:,.2f} kWh")
        else:
            print(f"\n❌ Extraction method: None (extraction failed)")
        
        if extraction_results.get('row_count', 0) > 1:
            print(f"\n⚠️  WARNING: {extraction_results['row_count']} rows found for RunPeriod meter")
            print(f"   This is unusual - RunPeriod should have 1 row")
            print(f"   Using MAX() is correct approach")
        
    else:
        print(f"❌ SQLite file not found: {sqlite_path}")
        print(f"   Errors: {extraction_results['errors']}")
    
    # Save results
    output_file = Path('test_outputs') / 'sqlite_extraction_diagnostic.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(extraction_results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()

