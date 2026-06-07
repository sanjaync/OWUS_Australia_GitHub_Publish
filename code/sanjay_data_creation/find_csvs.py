
import os
import pandas as pd

directory = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
required_columns = {'siteID', 'lat', 'lon'}

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        filepath = os.path.join(directory, filename)
        try:
            # Read only the header
            df = pd.read_csv(filepath, nrows=0)
            if required_columns.issubset(df.columns):
                print(f"Found: {filename}")
        except Exception as e:
            print(f"Error reading {filename}: {e}")
