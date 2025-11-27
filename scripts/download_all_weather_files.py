#!/usr/bin/env python3
"""
Download all weather files needed for benchmark tests.
"""

import requests
import shutil
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.location_fetcher import LocationFetcher


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
    
    return Path("/Applications/EnergyPlus-24-2-0/EnergyPlus installation files/WeatherData")


def download_from_energyplus_weather(city: str, state: str, weather_file_name: str, output_dir: Path) -> bool:
    """
    Download weather file from EnergyPlus weather database
    Uses direct download URLs
    """
    # EnergyPlus weather file URL patterns
    base_url = "https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA"
    
    # State folder mapping
    state_folders = {
        'PA': 'PA',
        'NY': 'NY',
        'WI': 'WI',
        'MA': 'MA',
    }
    
    state_folder = state_folders.get(state)
    if not state_folder:
        return False
    
    # Try direct EPW download
    url = f"{base_url}/{state_folder}/{weather_file_name}"
    
    output_path = output_dir / weather_file_name
    
    if output_path.exists():
        print(f"  ✓ Already exists: {weather_file_name}")
        return True
    
    try:
        print(f"  Downloading {weather_file_name}...")
        response = requests.get(url, timeout=60, allow_redirects=True)
        
        if response.status_code == 200:
            output_path.write_bytes(response.content)
            print(f"  ✓ Downloaded: {weather_file_name}")
            return True
        else:
            print(f"  ✗ HTTP {response.status_code}: {url}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def download_from_onebuilding(city: str, state: str, weather_file_name: str, output_dir: Path) -> bool:
    """Download from OneBuilding.org as fallback"""
    # OneBuilding URL pattern
    base_url = "https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America"
    
    state_folders = {
        'PA': 'PA_Pennsylvania',
        'NY': 'NY_New_York',
        'WI': 'WI_Wisconsin',
        'MA': 'MA_Massachusetts',
    }
    
    state_folder = state_folders.get(state)
    if not state_folder:
        return False
    
    # Try ZIP download
    zip_name = weather_file_name.replace('.epw', '.zip')
    url = f"{base_url}/{state_folder}/{zip_name}"
    
    output_path = output_dir / weather_file_name
    
    if output_path.exists():
        print(f"  ✓ Already exists: {weather_file_name}")
        return True
    
    try:
        print(f"  Downloading {zip_name} from OneBuilding...")
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                epw_files = [f for f in z.namelist() if f.endswith('.epw')]
                if epw_files:
                    epw_content = z.read(epw_files[0])
                    output_path.write_bytes(epw_content)
                    print(f"  ✓ Downloaded: {weather_file_name}")
                    return True
                else:
                    print(f"  ✗ No EPW file in ZIP")
                    return False
        else:
            print(f"  ✗ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Download all weather files needed for benchmark tests"""
    print("="*80)
    print("DOWNLOADING WEATHER FILES FOR BENCHMARK TESTS")
    print("="*80)
    
    # Load test data
    test_file = Path("artifacts/leed_benchmark_tests/benchmark_tests_combined.json")
    if not test_file.exists():
        print("❌ Test file not found")
        return 1
    
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    # Find directories
    ep_weather_dir = find_energyplus_weather_dir()
    project_weather_dir = Path("artifacts/desktop_files/weather")
    project_weather_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nEnergyPlus Weather Directory: {ep_weather_dir}")
    print(f"Project Weather Directory: {project_weather_dir}")
    
    # Get weather files needed
    print("\n" + "="*80)
    print("DETERMINING WEATHER FILES NEEDED")
    print("="*80)
    
    location_fetcher = LocationFetcher()
    weather_files_needed = {}
    
    for i, test in enumerate(data['tests'], 1):
        print(f"\nTest {i}: {test.get('building_name', test['pdf_filename'])}")
        
        address = test.get('address')
        if not address:
            print(f"  ✗ No address")
            continue
        
        print(f"  Address: {address}")
        
        # Extract city/state
        import re
        match = re.search(r',\s*([^,]+?),\s*([A-Z]{2})(?:\s+\d{5})?', address)
        if not match:
            match = re.search(r'^([^,]+?),\s*([A-Z]{2})\b', address)
        
        if match:
            city = match.group(1).strip()
            state = match.group(2).strip()
            print(f"  City: {city}, State: {state}")
            
            # Use manual mapping (more reliable than geocoding)
            manual_mappings = {
                ('Johnstown', 'PA'): 'USA_PA_Pittsburgh-Allegheny.Co.AP.725200_TMY3.epw',
                ('Tarrytown', 'NY'): 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
                ('Madison', 'WI'): 'USA_WI_Madison-Dane.Co.Rgnl.AP.726410_TMY3.epw',
                ('Peekskill', 'NY'): 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
                ('Athol', 'MA'): 'USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw',
            }
            
            # Also check if city name contains these keywords
            city_lower = city.lower()
            if 'peekskill' in city_lower or 'main st' in city_lower:
                weather_file = 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw'
            else:
                key = (city, state)
                weather_file = manual_mappings.get(key)
            
            if weather_file:
                weather_files_needed[i] = {
                    'address': address,
                    'city': city,
                    'state': state,
                    'weather_file': weather_file,
                    'test': test
                }
                print(f"  ✓ Weather file: {weather_file}")
            else:
                print(f"  ✗ Could not determine weather file for {city}, {state}")
    
    # Download weather files
    print("\n" + "="*80)
    print("DOWNLOADING WEATHER FILES")
    print("="*80)
    
    downloaded = []
    already_existed = []
    failed = []
    
    for test_num, info in weather_files_needed.items():
        weather_file = info['weather_file']
        city = info['city']
        state = info['state']
        
        print(f"\nTest {test_num}: {city}, {state}")
        print(f"  Weather file: {weather_file}")
        
        # Check if already exists in EnergyPlus directory
        ep_path = ep_weather_dir / weather_file
        if ep_path.exists():
            print(f"  ✓ Already in EnergyPlus directory")
            already_existed.append(weather_file)
            continue
        
        # Download to project directory first
        success = False
        
        # Try EnergyPlus GitHub first
        if not success:
            success = download_from_energyplus_weather(city, state, weather_file, project_weather_dir)
        
        # Try OneBuilding as fallback
        if not success:
            success = download_from_onebuilding(city, state, weather_file, project_weather_dir)
        
        if success:
            # Copy to EnergyPlus directory
            source = project_weather_dir / weather_file
            if source.exists():
                try:
                    shutil.copy2(source, ep_path)
                    print(f"  ✓ Copied to EnergyPlus directory")
                    downloaded.append(weather_file)
                except Exception as e:
                    print(f"  ⚠️  Downloaded but couldn't copy: {e}")
                    downloaded.append(weather_file)
            else:
                print(f"  ⚠️  Downloaded but file not found at {source}")
        else:
            failed.append(weather_file)
            print(f"  ✗ Failed to download")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nTotal weather files needed: {len(weather_files_needed)}")
    print(f"✓ Downloaded: {len(downloaded)}")
    print(f"✓ Already existed: {len(already_existed)}")
    print(f"✗ Failed: {len(failed)}")
    
    if downloaded:
        print("\nDownloaded files:")
        for f in downloaded:
            print(f"  - {f}")
    
    if already_existed:
        print("\nAlready existed:")
        for f in already_existed:
            print(f"  - {f}")
    
    if failed:
        print("\nFailed to download:")
        for f in failed:
            print(f"  - {f}")
        print("\n⚠️  You may need to download these manually from:")
        print("   https://energyplus.net/weather")
    
    print("\n" + "="*80)
    print("✓ Weather files setup complete!")
    print("="*80)
    
    return 0 if len(failed) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

