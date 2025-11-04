#!/usr/bin/env python3
"""
Download weather files from NREL for cities with known building energy data.
"""

import requests
import os
from pathlib import Path

# NREL TMY3 weather file locations
NREL_BASE_URL = "https://data.nrel.gov/system/files/68/"

# Weather files we need (TMY3 format)
WEATHER_FILES = {
    'Chicago': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/IL/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
        'filename': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    },
    'New_York': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/NY/USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw',
        'filename': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw'
    },
    'San_Francisco': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/CA/USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw',
        'filename': 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'
    },
    'Boston': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/MA/USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw',
        'filename': 'USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw'
    },
    'Seattle': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/WA/USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3.epw',
        'filename': 'USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3.epw'
    },
    'Los_Angeles': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/CA/USA_CA_Los.Angeles.Intl.AP.722950_TMY3.epw',
        'filename': 'USA_CA_Los.Angeles.Intl.AP.722950_TMY3.epw'
    },
    'Miami': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/FL/USA_FL_Miami.Intl.AP.722020_TMY3.epw',
        'filename': 'USA_FL_Miami.Intl.AP.722020_TMY3.epw'
    },
    'Denver': {
        'url': 'https://github.com/NREL/EnergyPlusWeatherData/raw/master/north_and_central_america_wmo_region_4/USA/CO/USA_CO_Denver-Aurora-Buckley.AFB.724695_TMY3.epw',
        'filename': 'USA_CO_Denver-Aurora-Buckley.AFB.724695_TMY3.epw'
    }
}

def download_weather_file(city_name: str, url: str, filename: str, output_dir: str = "artifacts/desktop_files/weather"):
    """Download a weather file from NREL"""
    output_path = Path(output_dir) / filename
    
    # Skip if already exists
    if output_path.exists():
        print(f"✓ {city_name}: Already exists ({filename})")
        return str(output_path)
    
    print(f"Downloading {city_name} weather file...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ {city_name}: Downloaded ({filename})")
        return str(output_path)
    except Exception as e:
        print(f"✗ {city_name}: Error downloading - {e}")
        return None

def main():
    """Download all weather files"""
    print("="*70)
    print("DOWNLOADING WEATHER FILES FROM NREL")
    print("="*70)
    print()
    
    downloaded = []
    skipped = []
    failed = []
    
    for city, info in WEATHER_FILES.items():
        result = download_weather_file(city, info['url'], info['filename'])
        if result:
            if "Already exists" in result:
                skipped.append(city)
            else:
                downloaded.append(city)
        else:
            failed.append(city)
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✓ Downloaded: {len(downloaded)}")
    print(f"⊘ Skipped (already exists): {len(skipped)}")
    print(f"✗ Failed: {len(failed)}")
    print()
    
    if downloaded:
        print("Downloaded files:")
        for city in downloaded:
            print(f"  - {city}")
    if skipped:
        print("Skipped files:")
        for city in skipped:
            print(f"  - {city}")
    if failed:
        print("Failed files:")
        for city in failed:
            print(f"  - {city}")

if __name__ == "__main__":
    main()

