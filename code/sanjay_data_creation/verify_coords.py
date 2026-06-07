
import os
import pandas as pd
import numpy as np

directory = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
target_site = 'AU-TTE'
expected_lat = -22.287
expected_lon = 133.64

files_to_check = [
    'ozflux_modis_igbp_pft.csv',
    'ozflux_soil_texture_soil_sensor.csv',
    'ozflux_modis_climatology.csv',
    'ozflux_modis_daily.csv',
    'ozflux_rootdepth_paper.csv',
    'ozflux_metadata.csv',
    'ozflux_vegetation_fraction.csv',
    'ozflux_Köppen_climate_classification.csv',
    'site_paths.csv'
]

all_correct = True

for filename in files_to_check:
    filepath = os.path.join(directory, filename)
    try:
        df = pd.read_csv(filepath)
        row = df[df['siteID'] == target_site]
        if not row.empty:
            lat = row.iloc[0]['lat']
            lon = row.iloc[0]['lon']
            
            # Use np.isclose for float comparison to avoid precision issues
            if np.isclose(lat, expected_lat) and np.isclose(lon, expected_lon):
                print(f"Verified {filename}: OK")
            else:
                print(f"FAILED {filename}: Expected ({expected_lat}, {expected_lon}), got ({lat}, {lon})")
                all_correct = False
        else:
            print(f"FAILED {filename}: Site {target_site} not found")
            all_correct = False
    except Exception as e:
        print(f"Error checking {filename}: {e}")
        all_correct = False

if all_correct:
    print("\nALL FILES VERIFIED SUCCESSFULLY.")
else:
    print("\nVERIFICATION FAILED.")
