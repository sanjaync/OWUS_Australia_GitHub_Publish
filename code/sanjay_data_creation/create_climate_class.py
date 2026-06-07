import pandas as pd
import os

# Input Files
SITE_PATHS_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/site_paths.csv"
EXCEL_FILE = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/OWUS_australia_fluxtower_updated.xlsx"

# Output File
OUTPUT_FILE = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_Köppen_climate_classification.csv"

def main():
    try:
        # Read Site Paths CSV
        print(f"Reading {SITE_PATHS_FILE}...")
        df_sites = pd.read_csv(SITE_PATHS_FILE)
        
        # Read Excel File
        print(f"Reading {EXCEL_FILE}...")
        df_climate = pd.read_excel(EXCEL_FILE)
        
        # Merge Data
        # Mapping: CSV 'original_site' -> Excel 'site'
        print("Merging data...")
        merged_df = pd.merge(
            df_sites, 
            df_climate, 
            left_on="original_site", 
            right_on="site", 
            how="left"
        )
        
        # Check for missing matches
        missing = merged_df[merged_df["KG_Code"].isna()]
        if not missing.empty:
            print(f"Warning: {len(missing)} sites matched no climate data:")
            print(missing["original_site"].tolist())
            
        # Select and Rename Columns if needed (though we just need specific columns)
        # Desired: siteID,original_site,lat,lon,KG_Code,KG_Label
        # Note: 'lat' and 'lon' exist in both potentially? 
        # df_sites has 'lat', 'lon'. df_climate has 'latitude', 'longitude'.
        # We stick to df_sites 'lat', 'lon' as primary.
        
        output_columns = ["siteID", "original_site", "lat", "lon", "KG_Code", "KG_Label"]
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Write to CSV
        print(f"Writing to {OUTPUT_FILE}...")
        merged_df[output_columns].to_csv(OUTPUT_FILE, index=False)
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
