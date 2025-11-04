#!/usr/bin/env python3
import os, sys, subprocess, time
sys.path.insert(0, '.')

print("Quick Final Test")
print("="*60)

# Generate IDF
from main import IDFCreator
creator = IDFCreator(professional=True, enhanced=True)

idf = creator.create_idf(
    '123 Main St, Chicago, IL',
    user_params={'building_type':'Office', 'stories':10, 'year_built':1995, 'floor_area_per_story_m2':1500},
    output_path='test_outputs/quick.idf'
)

# Check zones
import re
with open(idf, 'r') as f:
    c = f.read()
zones = c.count('Zone,')
surfaces = c.count('BuildingSurface:Detailed,')
floors = len(re.findall(r'_Floor,', c))

print(f'Zones: {zones}, Surfaces: {surfaces}, Floors: {floors}')
print(f'Surf/zone: {surfaces/zones:.1f}, Cover: {floors/zones*100:.0f}%')

# Quick simulation
epw = 'artifacts/desktop_files/weather/artifacts/desktop_files/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
os.makedirs('test_outputs/quick_sim', exist_ok=True)

print('Running simulation...')
subprocess.run(['/usr/local/bin/energyplus', '-w', epw, '-d', 'test_outputs/quick_sim', idf], 
              capture_output=True, timeout=120)

# Check if completed
if os.path.exists('test_outputs/quick_sim/eplusout.err'):
    with open('test_outputs/quick_sim/eplusout.err', 'r') as f:
        err_text = f.read()
    
    if 'Successfully' in err_text or 'Completed' in err_text:
        print('✅ Success')
        # Get CSV
        if os.path.exists('test_outputs/quick_sim/eplustbl.csv'):
            with open('test_outputs/quick_sim/eplustbl.csv', 'r') as f:
                for line in f:
                    if 'Total Site Energy' in line:
                        parts = line.split(',')
                        gj = float(parts[2])
                        mj_m2 = float(parts[3])
                        area = (gj*1000)/mj_m2
                        kbtu = (mj_m2/1000)*277.778*3.412/10.764
                        print(f'Area: {area:.0f} m² (expected: 15000)')
                        print(f'EUI: {kbtu:.1f} kBtu/ft²')
                        print(f'Eff: {area/15000*100:.1f}%')
                        break
    else:
        # Count errors
        severe = err_text.count('** Severe  **')
        print(f'Failed: {severe} severe errors')
else:
    print('❌ No error file')


