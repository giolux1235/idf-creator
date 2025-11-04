#!/usr/bin/env python3
"""
Quick Status Check for IDF Creator
Simple script to quickly check if the system is ready to use
"""

import sys
from pathlib import Path

def check_quick_status():
    """Quick status check"""
    print("🔍 Quick Status Check for IDF Creator\n")
    
    issues = []
    warnings = []
    
    # Check config file
    if not Path('config.yaml').exists():
        issues.append("Missing config.yaml")
    else:
        print("✓ Configuration file found")
    
    # Check source directory
    if not Path('src').exists():
        issues.append("Missing src directory")
    else:
        print("✓ Source directory found")
    
    # Check main module
    try:
        from main import IDFCreator
        print("✓ Main module can be imported")
    except Exception as e:
        issues.append(f"Cannot import main module: {e}")
    
    # Check key components
    components = [
        ('src.idf_generator', 'IDFGenerator'),
        ('src.location_fetcher', 'LocationFetcher'),
    ]
    
    for module_path, component_name in components:
        try:
            module = __import__(module_path, fromlist=[component_name])
            getattr(module, component_name)
            print(f"✓ {component_name} available")
        except Exception as e:
            issues.append(f"Cannot import {component_name}: {e}")
    
    # Check output directory
    output_dir = Path('artifacts/desktop_files/idf')
    if not output_dir.exists():
        warnings.append(f"Output directory {output_dir} does not exist (will be created)")
    else:
        print(f"✓ Output directory exists: {output_dir}")
    
    # Check weather files (optional)
    weather_dir = Path('artifacts/desktop_files/weather')
    if weather_dir.exists():
        epw_count = len(list(weather_dir.glob('*.epw')))
        if epw_count > 0:
            print(f"✓ {epw_count} weather file(s) found")
        else:
            warnings.append("Weather directory exists but no EPW files found")
    else:
        warnings.append("Weather directory not found (weather files optional)")
    
    # Summary
    print("\n" + "="*50)
    if issues:
        print("❌ STATUS: ISSUES FOUND")
        print("\nIssues:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    elif warnings:
        print("⚠️  STATUS: READY (with warnings)")
        print("\nWarnings:")
        for warning in warnings:
            print(f"  • {warning}")
        return True
    else:
        print("✅ STATUS: READY")
        print("All critical components are available")
        return True


if __name__ == '__main__':
    success = check_quick_status()
    sys.exit(0 if success else 1)

