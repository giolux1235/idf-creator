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
        'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/IL_Illinois/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.zip',
        'filename': 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    },
    'New_York': {
        'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/NY_New_York/USA_NY_New.York-LaGuardia.AP.725030_TMY3.zip',
        'filename': 'USA_NY_New.York.LaGuardia.AP.725030_TMY3.epw'
    },
    'San_Francisco': {
        'url': 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/USA_United_States_of_America/CA_California/USA_CA_San.Francisco.Intl.AP.724940_TMY3.zip',
        'filename': 'USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw'
    }
}

def download_weather_file(city_name: str, url: str, filename: str, output_dir: str = "artifacts/desktop_files/weather"):
    """Download a weather file from OneBuilding (ZIP) or direct URL"""
    output_path = Path(output_dir) / filename
    
    # Skip if already exists
    if output_path.exists():
        print(f"✓ {city_name}: Already exists ({filename})")
        return str(output_path)
    
    print(f"Downloading {city_name} weather file...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle ZIP files
        if url.endswith('.zip'):
            import zipfile
            import io
            
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Find the EPW file in the zip
                epw_files = [f for f in z.namelist() if f.endswith('.epw')]
                if not epw_files:
                    raise ValueError("No EPW file found in ZIP archive")
                
                # Extract the first EPW file
                epw_content = z.read(epw_files[0])
                
                with open(output_path, 'wb') as f:
                    f.write(epw_content)
        else:
            # Direct download
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

