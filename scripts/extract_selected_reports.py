#!/usr/bin/env python3
"""Extract data from 5 selected promising LEED reports"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.extract_leed_reports import LEEDReportExtractor


def main():
    # Select promising reports
    downloads_dir = Path('/Users/giovanniamenta/Downloads')
    leed_dir = [d for d in downloads_dir.glob('*LEED*') if d.is_dir()][0]
    
    # Select reports that are likely to have complete data
    # Replaced MTES (no address) with 74 Mount Auburn Street (has address)
    promising = [
        '19_0307-Arbutus-Park-Manor-Level-II-Energy-Audit-Report.pdf',
        '419363-2-ASHRAE-Level-2-Audit-Franklin-Towers-Tarrytown-NY-4-22-20-002.pdf',
        'Energy-Audit-Madison-Town-Building-2010.pdf',
        'EAc2.1 StopWaste_ASHRAE Level ll Audit_V2.pdf',  # Replaced MTES - has address and energy data
        'Peekskill-Energy-Audit-report-2021-1.pdf',
    ]
    
    selected = []
    for pdf_name in promising:
        pdf_path = leed_dir / pdf_name
        if pdf_path.exists():
            selected.append(str(pdf_path))
    
    print("="*80)
    print(f"EXTRACTING DATA FROM {len(selected)} SELECTED REPORTS")
    print("="*80)
    
    all_data = []
    for i, pdf_path in enumerate(selected, 1):
        print(f"\n[{i}/{len(selected)}] {Path(pdf_path).name}")
        print("-" * 80)
        try:
            extractor = LEEDReportExtractor(pdf_path)
            data = extractor.extract_all_data()
            all_data.append(data)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results
    output_dir = Path("artifacts/leed_benchmark_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, data in enumerate(all_data, 1):
        test_file = output_dir / f"benchmark_test_{i}.json"
        with open(test_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved: {test_file}")
    
    combined_file = output_dir / "benchmark_tests_combined.json"
    with open(combined_file, 'w') as f:
        json.dump({
            'extraction_date': str(Path.cwd()),
            'total_tests': len(all_data),
            'tests': all_data
        }, f, indent=2)
    
    print(f"\n✓ Saved combined: {combined_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    for i, data in enumerate(all_data, 1):
        print(f"\nTest {i}:")
        print(f"  File: {data['pdf_filename']}")
        if 'building_name' in data:
            print(f"  Building: {data['building_name']}")
        if 'address' in data:
            print(f"  Address: {data['address']}")
        if 'area_sqft' in data:
            print(f"  Area: {data['area_sqft']:,.0f} sqft")
        if 'floors' in data:
            print(f"  Floors: {data['floors']}")
        if 'year_built' in data:
            print(f"  Year Built: {data['year_built']}")
        if 'eui_kbtu_sqft' in data:
            print(f"  EUI: {data['eui_kbtu_sqft']:.1f} kBtu/sqft")
        if 'annual_electric_kwh' in data:
            print(f"  Annual Electric: {data['annual_electric_kwh']:,.0f} kWh")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

