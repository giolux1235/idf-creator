#!/usr/bin/env python3
"""
Diagnostic tool for facility meter implementation issues.

This tool checks:
1. Whether facility meters appear in MTR files
2. Whether meters appear in SQLite database
3. How many rows exist for RunPeriod meters
4. Whether values are cumulative or timestep-based
5. Compares SUM vs MAX for RunPeriod data
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def check_mtr_file(mtr_path: str) -> Dict:
    """Check if facility meters appear in MTR file."""
    results = {
        'file_exists': os.path.exists(mtr_path),
        'electricity_found': False,
        'natural_gas_found': False,
        'meter_lines': [],
        'total_meters': 0
    }
    
    if not results['file_exists']:
        return results
    
    try:
        with open(mtr_path, 'r') as f:
            lines = f.readlines()
        
        results['total_lines'] = len(lines)
        
        for i, line in enumerate(lines):
            if 'Electricity:Facility' in line:
                results['electricity_found'] = True
                results['meter_lines'].append({
                    'line_num': i + 1,
                    'content': line.strip(),
                    'meter': 'Electricity:Facility'
                })
            
            if 'NaturalGas:Facility' in line:
                results['natural_gas_found'] = True
                results['meter_lines'].append({
                    'line_num': i + 1,
                    'content': line.strip(),
                    'meter': 'NaturalGas:Facility'
                })
            
            # Count total meters (look for meter header lines)
            if line.strip().startswith('61,') or 'RunPeriod' in line:
                results['total_meters'] += 1
    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def check_sqlite_meters(sqlite_path: str) -> Dict:
    """Check facility meters in SQLite database."""
    results = {
        'file_exists': os.path.exists(sqlite_path),
        'electricity_found': False,
        'natural_gas_found': False,
        'electricity_data': {},
        'natural_gas_data': {},
        'tables': [],
        'errors': []
    }
    
    if not results['file_exists']:
        return results
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        results['tables'] = [row[0] for row in cursor.fetchall()]
        
        # Check for Electricity:Facility meter
        meter_queries = [
            # ReportMeterDataDictionary
            """
            SELECT 
                m.ReportMeterDataDictionaryIndex,
                m.Name,
                m.ReportingFrequency,
                COUNT(d.Value) as row_count,
                MIN(d.Value) as min_value,
                MAX(d.Value) as max_value,
                SUM(d.Value) as sum_value,
                AVG(d.Value) as avg_value
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name = 'Electricity:Facility'
            AND m.ReportingFrequency = 'RunPeriod'
            GROUP BY m.ReportMeterDataDictionaryIndex, m.Name, m.ReportingFrequency
            """,
            # ReportMeterDictionary
            """
            SELECT 
                m.ReportMeterDictionaryIndex,
                m.Name,
                m.ReportingFrequency,
                COUNT(d.Value) as row_count,
                MIN(d.Value) as min_value,
                MAX(d.Value) as max_value,
                SUM(d.Value) as sum_value,
                AVG(d.Value) as avg_value
            FROM ReportMeterData d
            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
            WHERE m.Name = 'Electricity:Facility'
            AND m.ReportingFrequency = 'RunPeriod'
            GROUP BY m.ReportMeterDictionaryIndex, m.Name, m.ReportingFrequency
            """
        ]
        
        for query in meter_queries:
            try:
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    results['electricity_found'] = True
                    results['electricity_data'] = {
                        'index': row[0],
                        'name': row[1],
                        'frequency': row[2],
                        'row_count': row[3],
                        'min_value_j': row[4],
                        'max_value_j': row[5],
                        'sum_value_j': row[6],
                        'avg_value_j': row[7],
                        'max_value_kwh': row[5] / 3600000.0 if row[5] else None,
                        'sum_value_kwh': row[6] / 3600000.0 if row[6] else None
                    }
                    break
            except Exception as e:
                results['errors'].append(f"Electricity query error: {str(e)}")
                continue
        
        # Check for NaturalGas:Facility meter
        gas_queries = [
            """
            SELECT 
                m.ReportMeterDataDictionaryIndex,
                m.Name,
                m.ReportingFrequency,
                COUNT(d.Value) as row_count,
                MIN(d.Value) as min_value,
                MAX(d.Value) as max_value,
                SUM(d.Value) as sum_value,
                AVG(d.Value) as avg_value
            FROM ReportMeterData d
            JOIN ReportMeterDataDictionary m ON d.ReportMeterDataDictionaryIndex = m.ReportMeterDataDictionaryIndex
            WHERE m.Name = 'NaturalGas:Facility'
            AND m.ReportingFrequency = 'RunPeriod'
            GROUP BY m.ReportMeterDataDictionaryIndex, m.Name, m.ReportingFrequency
            """,
            """
            SELECT 
                m.ReportMeterDictionaryIndex,
                m.Name,
                m.ReportingFrequency,
                COUNT(d.Value) as row_count,
                MIN(d.Value) as min_value,
                MAX(d.Value) as max_value,
                SUM(d.Value) as sum_value,
                AVG(d.Value) as avg_value
            FROM ReportMeterData d
            JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
            WHERE m.Name = 'NaturalGas:Facility'
            AND m.ReportingFrequency = 'RunPeriod'
            GROUP BY m.ReportMeterDictionaryIndex, m.Name, m.ReportingFrequency
            """
        ]
        
        for query in gas_queries:
            try:
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    results['natural_gas_found'] = True
                    results['natural_gas_data'] = {
                        'index': row[0],
                        'name': row[1],
                        'frequency': row[2],
                        'row_count': row[3],
                        'min_value_j': row[4],
                        'max_value_j': row[5],
                        'sum_value_j': row[6],
                        'avg_value_j': row[7],
                        'max_value_kwh': row[5] / 3600000.0 if row[5] else None,
                        'sum_value_kwh': row[6] / 3600000.0 if row[6] else None
                    }
                    break
            except Exception as e:
                results['errors'].append(f"NaturalGas query error: {str(e)}")
                continue
        
        # Get all RunPeriod meters for comparison
        cursor.execute("""
            SELECT Name, COUNT(*) as count
            FROM ReportMeterDataDictionary
            WHERE ReportingFrequency = 'RunPeriod'
            GROUP BY Name
            ORDER BY Name
        """)
        results['all_runperiod_meters'] = cursor.fetchall()
        
        conn.close()
    
    except Exception as e:
        results['errors'].append(f"SQLite connection error: {str(e)}")
    
    return results


def check_idf_file(idf_path: str) -> Dict:
    """Check if facility meters are in IDF file."""
    results = {
        'file_exists': os.path.exists(idf_path),
        'electricity_meter_found': False,
        'natural_gas_meter_found': False,
        'meter_lines': []
    }
    
    if not results['file_exists']:
        return results
    
    try:
        with open(idf_path, 'r') as f:
            content = f.read()
        
        # Check for Output:Meter objects
        if 'Output:Meter' in content:
            lines = content.split('\n')
            in_meter_block = False
            current_meter = None
            
            for i, line in enumerate(lines):
                if 'Output:Meter,' in line:
                    in_meter_block = True
                    current_meter = {'line': i + 1, 'content': []}
                
                if in_meter_block:
                    current_meter['content'].append(line.strip())
                    
                    if 'Electricity:Facility' in line:
                        results['electricity_meter_found'] = True
                        current_meter['type'] = 'Electricity:Facility'
                        results['meter_lines'].append(current_meter)
                    
                    if 'NaturalGas:Facility' in line:
                        results['natural_gas_meter_found'] = True
                        current_meter['type'] = 'NaturalGas:Facility'
                        results['meter_lines'].append(current_meter)
                    
                    # End of meter block (semicolon)
                    if line.strip().endswith(';'):
                        if current_meter and 'type' not in current_meter:
                            results['meter_lines'].append(current_meter)
                        in_meter_block = False
                        current_meter = None
    
    except Exception as e:
        results['error'] = str(e)
    
    return results


def main():
    """Main diagnostic function."""
    if len(sys.argv) < 2:
        print("Usage: python diagnose_facility_meters.py <simulation_output_dir>")
        print("  or:   python diagnose_facility_meters.py <idf_file> <mtr_file> <sqlite_file>")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # Single directory argument
        output_dir = Path(sys.argv[1])
        idf_path = output_dir / "in.idf"
        mtr_path = output_dir / "eplusout.mtr"
        sqlite_path = output_dir / "eplusout.sql"
    else:
        # Separate file arguments
        idf_path = Path(sys.argv[1])
        mtr_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        sqlite_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    print("=" * 80)
    print("FACILITY METER DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Check IDF file
    print("1. CHECKING IDF FILE")
    print("-" * 80)
    idf_results = check_idf_file(str(idf_path))
    if idf_results['file_exists']:
        print(f"✅ IDF file found: {idf_path}")
        print(f"   Electricity:Facility meter: {'✅ FOUND' if idf_results['electricity_meter_found'] else '❌ NOT FOUND'}")
        print(f"   NaturalGas:Facility meter: {'✅ FOUND' if idf_results['natural_gas_meter_found'] else '❌ NOT FOUND'}")
        if idf_results['meter_lines']:
            print(f"\n   Meter definitions found:")
            for meter in idf_results['meter_lines']:
                print(f"   - Line {meter['line']}: {meter.get('type', 'Unknown')}")
                for line in meter['content'][:3]:  # Show first 3 lines
                    print(f"     {line}")
    else:
        print(f"❌ IDF file not found: {idf_path}")
    print()
    
    # Check MTR file
    if mtr_path:
        print("2. CHECKING MTR FILE")
        print("-" * 80)
        mtr_results = check_mtr_file(str(mtr_path))
        if mtr_results['file_exists']:
            print(f"✅ MTR file found: {mtr_path}")
            print(f"   Electricity:Facility meter: {'✅ FOUND' if mtr_results['electricity_found'] else '❌ NOT FOUND'}")
            print(f"   NaturalGas:Facility meter: {'✅ FOUND' if mtr_results['natural_gas_found'] else '❌ NOT FOUND'}")
            print(f"   Total meter lines: {mtr_results['total_meters']}")
            if mtr_results['meter_lines']:
                print(f"\n   Meter entries found:")
                for meter in mtr_results['meter_lines'][:5]:  # Show first 5
                    print(f"   - Line {meter['line_num']}: {meter['meter']}")
                    print(f"     {meter['content'][:100]}")
        else:
            print(f"❌ MTR file not found: {mtr_path}")
        print()
    
    # Check SQLite file
    if sqlite_path:
        print("3. CHECKING SQLITE DATABASE")
        print("-" * 80)
        sqlite_results = check_sqlite_meters(str(sqlite_path))
        if sqlite_results['file_exists']:
            print(f"✅ SQLite file found: {sqlite_path}")
            print(f"   Tables found: {', '.join(sqlite_results['tables'][:10])}")
            print()
            
            # Electricity meter
            if sqlite_results['electricity_found']:
                print(f"✅ Electricity:Facility meter found in SQLite")
                data = sqlite_results['electricity_data']
                print(f"   Row count: {data['row_count']}")
                print(f"   Min value: {data['min_value_j']:,.0f} J ({data['min_value_j']/3600000.0:,.2f} kWh)")
                print(f"   Max value: {data['max_value_j']:,.0f} J ({data['max_value_kwh']:,.2f} kWh)")
                print(f"   Sum value: {data['sum_value_j']:,.0f} J ({data['sum_value_kwh']:,.2f} kWh)")
                if data['row_count'] > 1:
                    print(f"   ⚠️  WARNING: Multiple rows found for RunPeriod meter!")
                    print(f"      This suggests timestep data. Use MAX() not SUM().")
                    print(f"      MAX/SUM ratio: {data['max_value_j']/data['sum_value_j']*data['row_count']:.2f}x")
                else:
                    print(f"   ✅ Single row (as expected for RunPeriod)")
                    print(f"      MAX() = SUM() = {data['max_value_j']:,.0f} J")
            else:
                print(f"❌ Electricity:Facility meter NOT found in SQLite")
            print()
            
            # Natural gas meter
            if sqlite_results['natural_gas_found']:
                print(f"✅ NaturalGas:Facility meter found in SQLite")
                data = sqlite_results['natural_gas_data']
                print(f"   Row count: {data['row_count']}")
                print(f"   Min value: {data['min_value_j']:,.0f} J ({data['min_value_j']/3600000.0:,.2f} kWh)")
                print(f"   Max value: {data['max_value_j']:,.0f} J ({data['max_value_kwh']:,.2f} kWh)")
                print(f"   Sum value: {data['sum_value_j']:,.0f} J ({data['sum_value_kwh']:,.2f} kWh)")
                if data['row_count'] > 1:
                    print(f"   ⚠️  WARNING: Multiple rows found for RunPeriod meter!")
                    print(f"      This suggests timestep data. Use MAX() not SUM().")
                    print(f"      MAX/SUM ratio: {data['max_value_j']/data['sum_value_j']*data['row_count']:.2f}x")
                else:
                    print(f"   ✅ Single row (as expected for RunPeriod)")
                    print(f"      MAX() = SUM() = {data['max_value_j']:,.0f} J")
            else:
                print(f"❌ NaturalGas:Facility meter NOT found in SQLite")
            print()
            
            # All RunPeriod meters
            if sqlite_results.get('all_runperiod_meters'):
                print(f"All RunPeriod meters in database:")
                for name, count in sqlite_results['all_runperiod_meters'][:20]:
                    print(f"  - {name}: {count} row(s)")
            
            if sqlite_results['errors']:
                print(f"\n⚠️  Errors encountered:")
                for error in sqlite_results['errors']:
                    print(f"   {error}")
        else:
            print(f"❌ SQLite file not found: {sqlite_path}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    issues = []
    if idf_results['file_exists']:
        if not idf_results['electricity_meter_found']:
            issues.append("❌ Electricity:Facility meter missing from IDF")
        if not idf_results['natural_gas_meter_found']:
            issues.append("❌ NaturalGas:Facility meter missing from IDF")
    
    if mtr_path and mtr_results.get('file_exists'):
        if not mtr_results['electricity_found']:
            issues.append("❌ Electricity:Facility meter missing from MTR file")
        if not mtr_results['natural_gas_found']:
            issues.append("❌ NaturalGas:Facility meter missing from MTR file")
    
    if sqlite_path and sqlite_results.get('file_exists'):
        if not sqlite_results['electricity_found']:
            issues.append("❌ Electricity:Facility meter missing from SQLite")
        if not sqlite_results['natural_gas_found']:
            issues.append("❌ NaturalGas:Facility meter missing from SQLite")
        
        # Check for multiple rows issue
        if sqlite_results.get('electricity_data', {}).get('row_count', 0) > 1:
            issues.append("⚠️  Electricity:Facility has multiple rows - use MAX() not SUM()")
        if sqlite_results.get('natural_gas_data', {}).get('row_count', 0) > 1:
            issues.append("⚠️  NaturalGas:Facility has multiple rows - use MAX() not SUM()")
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No issues found - all meters are correctly configured!")
    
    print()


if __name__ == "__main__":
    main()



