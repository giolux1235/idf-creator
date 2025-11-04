#!/usr/bin/env python3
"""
Extract energy results from EnergyPlus SQL database
"""
import sys
import os
import sqlite3
from pathlib import Path


def extract_energy_from_sql(sql_file: str):
    """Extract energy consumption from EnergyPlus SQL database"""
    if not os.path.exists(sql_file):
        print(f"SQL file not found: {sql_file}")
        return None
    
    try:
        conn = sqlite3.connect(sql_file)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nTables in database: {[t[0] for t in tables]}")
        
        # Try to find time series data
        # EnergyPlus stores data in various tables
        energy_data = {}
        
        # Check ReportVariableData table
        try:
            cursor.execute("SELECT COUNT(*) FROM ReportVariableData;")
            count = cursor.fetchone()[0]
            print(f"ReportVariableData rows: {count}")
            
            # Get unique variable names
            cursor.execute("""
                SELECT DISTINCT v.VariableName, v.ReportingFrequency
                FROM ReportVariableData d
                JOIN ReportVariableDictionary v ON d.ReportVariableDictionaryIndex = v.ReportVariableDictionaryIndex
                WHERE v.VariableName LIKE '%Energy%' OR v.VariableName LIKE '%Electricity%'
                LIMIT 20;
            """)
            vars = cursor.fetchall()
            if vars:
                print(f"\nEnergy-related variables found:")
                for vname, freq in vars[:10]:
                    print(f"  - {vname} ({freq})")
        except Exception as e:
            print(f"Could not query ReportVariableData: {e}")
        
        # Try ReportMeterData
        try:
            cursor.execute("SELECT COUNT(*) FROM ReportMeterData;")
            count = cursor.fetchone()[0]
            print(f"\nReportMeterData rows: {count}")
            
            # Get meter names
            cursor.execute("""
                SELECT DISTINCT m.Name, m.ReportingFrequency
                FROM ReportMeterData d
                JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
                LIMIT 20;
            """)
            meters = cursor.fetchall()
            if meters:
                print(f"\nMeter names found:")
                for mname, freq in meters[:10]:
                    print(f"  - {mname} ({freq})")
        except Exception as e:
            print(f"Could not query ReportMeterData: {e}")
        
        # Get annual totals from meters
        try:
            cursor.execute("""
                SELECT 
                    m.Name,
                    SUM(d.Value) as Total
                FROM ReportMeterData d
                JOIN ReportMeterDictionary m ON d.ReportMeterDictionaryIndex = m.ReportMeterDictionaryIndex
                WHERE m.ReportingFrequency = 'RunPeriod'
                GROUP BY m.Name
                ORDER BY Total DESC;
            """)
            annual_totals = cursor.fetchall()
            if annual_totals:
                print(f"\nAnnual Energy Totals:")
                for name, total in annual_totals[:15]:
                    print(f"  {name}: {total:,.2f}")
                    energy_data[name] = total
        except Exception as e:
            print(f"Could not get annual totals: {e}")
        
        conn.close()
        return energy_data
        
    except Exception as e:
        print(f"Error reading SQL database: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Extract energy from Chicago and Austin simulations"""
    
    print("=" * 80)
    print("ENERGY EXTRACTION FROM SQL DATABASES")
    print("=" * 80)
    
    # Chicago
    print("\n1. Chicago Simulation:")
    chicago_sql = "artifacts/desktop_files/simulation/chicago/eplusout.sql"
    if os.path.exists(chicago_sql):
        energy = extract_energy_from_sql(chicago_sql)
        if energy:
            total = sum(v for v in energy.values() if v > 0)
            print(f"\n   Total Energy: {total:,.0f} (sum of all meters)")
    else:
        print(f"   SQL file not found: {chicago_sql}")
    
    # Austin
    print("\n2. Austin Simulation:")
    austin_sql = "artifacts/desktop_files/simulation/austin/eplusout.sql"
    if os.path.exists(austin_sql):
        energy = extract_energy_from_sql(austin_sql)
        if energy:
            total = sum(v for v in energy.values() if v > 0)
            print(f"\n   Total Energy: {total:,.0f} (sum of all meters)")
    else:
        print(f"   SQL file not found: {austin_sql}")


if __name__ == "__main__":
    main()



