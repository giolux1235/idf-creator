#!/usr/bin/env python3
"""
Extract data from multiple LEED reports and select the 5 best ones with most complete data.
"""

import json
import sys
from pathlib import Path
from scripts.extract_leed_reports import LEEDReportExtractor


def score_report_completeness(data: dict) -> int:
    """Score how complete a report's data is"""
    score = 0
    
    # Essential fields
    if 'address' in data and data['address']:
        score += 10
    if 'area_sqft' in data or 'area_m2' in data:
        score += 15
    if 'floors' in data:
        score += 10
    if 'year_built' in data:
        score += 10
    if 'building_type' in data:
        score += 5
    
    # Energy data (very important)
    if 'eui_kbtu_sqft' in data or 'eui_kwh_m2' in data:
        score += 20
    if 'annual_electric_kwh' in data:
        score += 15
    if 'total_site_energy_kwh' in data:
        score += 15
    if 'energy_breakdown_percent' in data:
        score += 10
    
    # Building name is nice to have
    if 'building_name' in data and data['building_name']:
        score += 5
    
    return score


def main():
    """Extract from multiple reports and select best 5"""
    print("="*80)
    print("EXTRACTING BEST REPORTS FOR BENCHMARKING")
    print("="*80)
    
    # Find LEED directory
    downloads_dir = Path("/Users/giovanniamenta/Downloads")
    leed_dirs = [d for d in downloads_dir.glob("*LEED*") if d.is_dir()]
    
    if not leed_dirs:
        print("❌ LEED directory not found")
        return 1
    
    leed_dir = leed_dirs[0]
    pdf_files = list(leed_dir.glob("*.pdf")) + list(leed_dir.glob("*.PDF"))
    
    print(f"\nFound {len(pdf_files)} PDF files")
    print("Processing reports to find the 5 most complete...")
    
    # Process all reports and score them
    all_reports = []
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {pdf_path.name[:60]}...")
        try:
            extractor = LEEDReportExtractor(str(pdf_path))
            data = extractor.extract_all_data()
            score = score_report_completeness(data)
            data['completeness_score'] = score
            all_reports.append(data)
            print(f"  Score: {score}/100")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    # Sort by completeness score (highest first)
    all_reports.sort(key=lambda x: x.get('completeness_score', 0), reverse=True)
    
    # Select top 5
    best_5 = all_reports[:5]
    
    print("\n" + "="*80)
    print("TOP 5 REPORTS SELECTED")
    print("="*80)
    
    for i, report in enumerate(best_5, 1):
        print(f"\nTest {i}: Score {report.get('completeness_score', 0)}/100")
        print(f"  File: {report['pdf_filename']}")
        if 'building_name' in report:
            print(f"  Building: {report['building_name']}")
        if 'address' in report:
            print(f"  Address: {report['address']}")
        if 'area_sqft' in report:
            print(f"  Area: {report['area_sqft']:,.0f} sqft")
        if 'floors' in report:
            print(f"  Floors: {report['floors']}")
        if 'eui_kbtu_sqft' in report:
            print(f"  EUI: {report['eui_kbtu_sqft']:.1f} kBtu/sqft")
    
    # Save best 5
    output_dir = Path("artifacts/leed_benchmark_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual test files
    for i, data in enumerate(best_5, 1):
        # Remove completeness_score before saving
        test_data = {k: v for k, v in data.items() if k != 'completeness_score'}
        test_file = output_dir / f"benchmark_test_{i}.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        print(f"\n✓ Saved: {test_file}")
    
    # Save combined file
    combined_data = {
        'extraction_date': str(Path.cwd()),
        'total_reports_processed': len(all_reports),
        'selected_tests': 5,
        'tests': [{k: v for k, v in r.items() if k != 'completeness_score'} for r in best_5]
    }
    
    combined_file = output_dir / "benchmark_tests_combined.json"
    with open(combined_file, 'w') as f:
        json.dump(combined_data, f, indent=2)
    
    print(f"\n✓ Saved combined: {combined_file}")
    print("\n" + "="*80)
    print("✅ Extraction complete!")
    print("="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())









