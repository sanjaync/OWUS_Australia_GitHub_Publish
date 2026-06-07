
import os
import pandas as pd

directory = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
target_site = 'AU-TTE'
new_lat = -22.287
new_lon = 133.64

files_to_update = [
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

for filename in files_to_update:
    filepath = os.path.join(directory, filename)
    try:
        df = pd.read_csv(filepath)
        if 'siteID' in df.columns and 'lat' in df.columns and 'lon' in df.columns:
            mask = df['siteID'] == target_site
            if mask.any():
                df.loc[mask, 'lat'] = new_lat
                df.loc[mask, 'lon'] = new_lon
                df.to_csv(filepath, index=False)
                print(f"Updated {filename}")
            else:
                print(f"Site {target_site} not found in {filename}")
        else:
            print(f"Skipping {filename}: missing required columns")
    except Exception as e:
        print(f"Error processing {filename}: {e}")
