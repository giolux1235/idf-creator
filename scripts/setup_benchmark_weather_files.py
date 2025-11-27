#!/usr/bin/env python3
"""
Extract missing addresses from benchmark tests and download required weather files.
Stores weather files in EnergyPlus weather folder.
"""

import json
import sys
import shutil
from pathlib import Path
import requests
import zipfile
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.location_fetcher import LocationFetcher
from scripts.extract_leed_reports import LEEDReportExtractor


def find_energyplus_weather_dir():
    """Find EnergyPlus weather directory"""
    possible_locations = [
        "/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData",
        "/Applications/EnergyPlus-23-2-0/EnergyPlus installation files/WeatherData",
        "/usr/share/EnergyPlus/weather",
        "/opt/EnergyPlus/weather",
        str(Path.home() / "EnergyPlus/weather"),
    ]
    
    for location in possible_locations:
        weather_dir = Path(location)
        if weather_dir.exists() and weather_dir.is_dir():
            return weather_dir
    
    # Return default location if not found
    return Path("/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData")


def fix_address_typos(address: str) -> str:
    """Fix common typos in addresses"""
    # Fix "reet" -> "Street" (but not if already "Street")
    address = address.replace("Main St reet", "Main Street")
    address = address.replace("St reet", "Street")
    address = address.replace("reet", "Street")
    # Fix double "Street"
    address = address.replace("StStreet", "Street")
    address = address.replace("StreetStreet", "Street")
    return address


def download_weather_file_from_onebuilding(city: str, state: str, output_dir: Path) -> tuple[str, bool]:
    """
    Download weather file from OneBuilding.org
    Returns: (filename, success)
    """
    # OneBuilding URL pattern
    base_url = "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America"
    
    # State code mapping
    state_codes = {
        'PA': 'PA_Pennsylvania',
        'NY': 'NY_New_York',
        'WI': 'WI_Wisconsin',
        'CT': 'CT_Connecticut',
        'MA': 'MA_Massachusetts',
    }
    
    state_folder = state_codes.get(state, f"{state}_{state}")
    
    # Try to find weather file URL
    # For now, we'll use a mapping of known cities to weather file names
    # Weather file mappings - using direct EPW URLs from OneBuilding
    city_weather_map = {
        ('Johnstown', 'PA'): {
            'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/PA_Pennsylvania/USA_PA_Pittsburgh-Allegheny.Co.AP.725200_TMY3.epw',
            'filename': 'USA_PA_Pittsburgh-Allegheny.Co.AP.725200_TMY3.epw',
            'is_zip': False
        },
        ('Tarrytown', 'NY'): {
            'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/NY_New_York/USA_NY_New.York-LaGuardia.AP.725030_TMY3.zip',
            'filename': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
            'is_zip': True
        },
        ('Peekskill', 'NY'): {
            'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/NY_New_York/USA_NY_New.York-LaGuardia.AP.725030_TMY3.zip',
            'filename': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
            'is_zip': True
        },
        ('Madison', 'WI'): {
            'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/WI_Wisconsin/USA_WI_Madison-Dane.Co.Rgnl.AP.726410_TMY3.zip',
            'filename': 'USA_WI_Madison-Dane.Co.Rgnl.AP.726410_TMY3.epw',
            'is_zip': True
        },
        ('Madison', 'CT'): {
            'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/CT_Connecticut/USA_CT_Bridgeport-Sikorsky.Mem.AP.725045_TMY3.zip',
            'filename': 'USA_CT_Bridgeport-Sikorsky.Mem.AP.725045_TMY3.epw',
            'is_zip': True
        },
    }
    
    # Try exact match first
    key = (city, state)
    if key in city_weather_map:
        info = city_weather_map[key]
    else:
        # Try to find closest match
        # For NY cities, use LaGuardia
        if state == 'NY':
            info = {
                'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/NY_New_York/USA_NY_New.York-LaGuardia.AP.725030_TMY3.zip',
                'filename': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
                'is_zip': True
            }
        # For PA cities, use Pittsburgh (closest major airport)
        elif state == 'PA':
            info = {
                'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/PA_Pennsylvania/USA_PA_Pittsburgh-Allegheny.Co.AP.725200_TMY3.epw',
                'filename': 'USA_PA_Pittsburgh-Allegheny.Co.AP.725200_TMY3.epw',
                'is_zip': False
            }
        else:
            return None, False
    
    output_path = output_dir / info['filename']
    
    # Check if already exists
    if output_path.exists():
        return str(output_path), True
    
    try:
        print(f"  Downloading weather file for {city}, {state}...")
        response = requests.get(info['url'], timeout=60)
        response.raise_for_status()
        
        if info.get('is_zip', True):
            # Extract EPW from ZIP
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                epw_files = [f for f in z.namelist() if f.endswith('.epw')]
                if not epw_files:
                    raise ValueError("No EPW file found in ZIP")
                
                epw_content = z.read(epw_files[0])
                output_path.write_bytes(epw_content)
        else:
            # Direct EPW file
            output_path.write_bytes(response.content)
        
        print(f"  ✓ Downloaded: {info['filename']}")
        return str(output_path), True
        
    except Exception as e:
        print(f"  ✗ Error downloading: {e}")
        return None, False


def get_weather_file_from_address(address: str, location_fetcher: LocationFetcher) -> tuple[str, bool]:
    """Get weather file name from address using location fetcher"""
    try:
        location_data = location_fetcher.fetch_location_data(address)
        weather_file = location_data.get('weather_file')
        if weather_file:
            return weather_file, True
    except Exception as e:
        print(f"  ⚠️  Error getting weather file: {e}")
    
    return None, False


def extract_missing_addresses():
    """Extract missing addresses from PDFs"""
    test_file = Path("artifacts/leed_benchmark_tests/benchmark_tests_combined.json")
    
    if not test_file.exists():
        print("❌ Test file not found")
        return {}
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    addresses = {}
    
    for i, test in enumerate(data['tests'], 1):
        pdf_path = test['pdf_path']
        
        if 'address' in test and test['address']:
            addresses[i] = test['address']
            print(f"Test {i}: ✓ Address found: {test['address']}")
        else:
            # Try to extract from PDF
            print(f"Test {i}: Extracting address from PDF...")
            try:
                extractor = LEEDReportExtractor(pdf_path)
                extractor.extract_all_pages()
                address = extractor.extract_address()
                
                if address:
                    addresses[i] = address
                    print(f"  ✓ Extracted: {address}")
                else:
                    # Infer from filename
                    filename = test['pdf_filename']
                    if 'Tarrytown' in filename:
                        addresses[i] = "Tarrytown, NY"
                        print(f"  → Inferred: Tarrytown, NY")
                    elif 'Madison' in filename:
                        # Try to determine which Madison
                        addresses[i] = "Madison, WI"  # Most common
                        print(f"  → Inferred: Madison, WI (most common)")
                    elif 'MTES' in filename:
                        # MTES could be in various locations, try to extract more
                        addresses[i] = None  # Will need manual lookup
                        print(f"  → Could not determine MTES location")
                    else:
                        addresses[i] = None
                        print(f"  ✗ Could not determine address")
            except Exception as e:
                print(f"  ✗ Error extracting: {e}")
                addresses[i] = None
    
    return addresses


def main():
    """Main function"""
    print("="*80)
    print("SETTING UP WEATHER FILES FOR BENCHMARK TESTS")
    print("="*80)
    
    # Find EnergyPlus weather directory
    ep_weather_dir = find_energyplus_weather_dir()
    print(f"\nEnergyPlus Weather Directory: {ep_weather_dir}")
    
    if not ep_weather_dir.exists():
        print(f"⚠️  Warning: EnergyPlus weather directory not found at {ep_weather_dir}")
        print("   Will use artifacts/desktop_files/weather instead")
        ep_weather_dir = Path("artifacts/desktop_files/weather")
        ep_weather_dir.mkdir(parents=True, exist_ok=True)
    
    # Also use project weather directory
    project_weather_dir = Path("artifacts/desktop_files/weather")
    project_weather_dir.mkdir(parents=True, exist_ok=True)
    
    # Load test data
    test_file = Path("artifacts/leed_benchmark_tests/benchmark_tests_combined.json")
    if not test_file.exists():
        print("❌ Test file not found. Run extract_selected_reports.py first.")
        return 1
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Extract missing addresses
    print("\n" + "="*80)
    print("EXTRACTING ADDRESSES")
    print("="*80)
    addresses = extract_missing_addresses()
    
    # Update test data with extracted addresses
    updated = False
    for i, test in enumerate(data['tests'], 1):
        if i in addresses and addresses[i] and 'address' not in test:
            test['address'] = addresses[i]
            updated = True
    
    if updated:
        with open(test_file, 'w') as f:
            json.dump(data, f, indent=2)
        print("\n✓ Updated test file with extracted addresses")
    
    # Get weather files for each test
    print("\n" + "="*80)
    print("GETTING WEATHER FILES")
    print("="*80)
    
    location_fetcher = LocationFetcher()
    weather_files_needed = {}
    
    for i, test in enumerate(data['tests'], 1):
        print(f"\nTest {i}: {test.get('building_name', test['pdf_filename'])}")
        
        address = test.get('address')
        if not address:
            print(f"  ✗ No address - cannot determine weather file")
            continue
        
        # Fix address typos
        address = fix_address_typos(address)
        print(f"  Address: {address}")
        
        # Extract city/state first
        import re
        # Try multiple patterns to extract city and state
        # Pattern 1: "..., City, State ZIP"
        match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})(?:\s+\d{5})?', address)
        if not match:
            # Pattern 2: "..., City, State"
            match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})\b', address)
        if not match:
            # Pattern 3: "City, State ZIP" (at start)
            match = re.search(r'^([^,]+?),\s*([A-Z]{2})(?:\s+\d{5})?', address)
        if not match:
            # Pattern 4: "City, State" (at start, no zip)
            match = re.search(r'^([^,]+?),\s*([A-Z]{2})\b', address)
        if not match:
            # Pattern 5: "Street City, State ZIP" - extract last city before state
            match = re.search(r'([A-Z][a-z]+(?:\.)?)\s+([A-Z]{2})(?:\s+\d{5})?', address)
            if match:
                # Extract city name (word before state)
                city_match = re.search(r'([A-Z][a-z]+(?:\.)?)\s+' + match.group(2) + r'(?:\s+\d{5})?', address)
                if city_match:
                    city = city_match.group(1)
                    state = match.group(2)
                    match = type('Match', (), {'group': lambda self, n: city if n == 1 else state})()
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            print(f"  → City: {city}, State: {state}")
            
            # Try to download weather file directly
            filepath, downloaded = download_weather_file_from_onebuilding(
                city, state, project_weather_dir
            )
            
            if downloaded and filepath:
                weather_file = Path(filepath).name
                weather_files_needed[i] = {
                    'address': address,
                    'weather_file': weather_file,
                    'test': test,
                    'filepath': filepath
                }
                print(f"  ✓ Weather file: {weather_file}")
            else:
                # Fallback: Try to get weather file name from address
                weather_file, success = get_weather_file_from_address(address, location_fetcher)
                if success and weather_file:
                    weather_files_needed[i] = {
                        'address': address,
                        'weather_file': weather_file,
                        'test': test
                    }
                    print(f"  ✓ Weather file (from geocoding): {weather_file}")
                else:
                    print(f"  ✗ Could not determine weather file")
        else:
            print(f"  ✗ Could not extract city/state from address")
    
    # Copy weather files to EnergyPlus directory
    print("\n" + "="*80)
    print("COPYING WEATHER FILES TO ENERGYPLUS DIRECTORY")
    print("="*80)
    
    copied = []
    skipped = []
    
    for test_num, info in weather_files_needed.items():
        weather_file = info['weather_file']
        
        # Source file
        if 'filepath' in info:
            source = Path(info['filepath'])
        else:
            source = project_weather_dir / weather_file
        
        # Destination
        dest = ep_weather_dir / weather_file
        
        if dest.exists():
            print(f"Test {test_num}: ✓ {weather_file} already exists")
            skipped.append(weather_file)
        elif source.exists():
            try:
                shutil.copy2(source, dest)
                print(f"Test {test_num}: ✓ Copied {weather_file}")
                copied.append(weather_file)
            except Exception as e:
                print(f"Test {test_num}: ✗ Error copying {weather_file}: {e}")
        else:
            print(f"Test {test_num}: ⚠️  {weather_file} not found at {source}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nWeather Files Needed: {len(weather_files_needed)}")
    print(f"Copied: {len(copied)}")
    print(f"Already Existed: {len(skipped)}")
    
    print("\nWeather Files Status:")
    for test_num, info in weather_files_needed.items():
        weather_file = info['weather_file']
        ep_path = ep_weather_dir / weather_file
        proj_path = project_weather_dir / weather_file
        
        status = "✓" if ep_path.exists() else "✗"
        print(f"  {status} Test {test_num}: {weather_file}")
        if ep_path.exists():
            print(f"      Location: {ep_path}")
    
    print(f"\n✓ Weather files setup complete!")
    print(f"  EnergyPlus directory: {ep_weather_dir}")
    print(f"  Project directory: {project_weather_dir}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

