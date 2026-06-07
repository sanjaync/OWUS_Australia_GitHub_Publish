import pandas as pd
import os

def main():
    base_dir = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
    site_paths_file = os.path.join(base_dir, 'site_paths.csv')
    ozflux_pft_file = os.path.join(base_dir, 'ozflux_pft.csv')

    print(f"Reading {site_paths_file}...")
    try:
        df_site_paths = pd.read_csv(site_paths_file)
    except FileNotFoundError:
        print(f"Error: Could not find {site_paths_file}")
        return

    print(f"Reading {ozflux_pft_file}...")
    try:
        df_pft = pd.read_csv(ozflux_pft_file)
    except FileNotFoundError:
        print(f"Error: Could not find {ozflux_pft_file}")
        return

    # Check columns
    if 'siteID' not in df_site_paths.columns or 'original_site' not in df_site_paths.columns:
        print("Error: site_paths.csv missing required columns (siteID, original_site)")
        return
    
    if 'original_site' not in df_pft.columns:
        print("Error: ozflux_pft.csv missing required column (original_site)")
        return

    # Extract mapping
    site_map = df_site_paths[['siteID', 'original_site']].drop_duplicates()

    # Merge
    # Using left join to preserve all rows in ozflux_pft
    print("Merging data...")
    merged_df = pd.merge(df_pft, site_map, on='original_site', how='left')

    # Reorder columns to have siteID first (optional but nice)
    cols = ['siteID'] + [c for c in merged_df.columns if c != 'siteID']
    merged_df = merged_df[cols]

    # Save
    print(f"Saving updated data to {ozflux_pft_file}...")
    merged_df.to_csv(ozflux_pft_file, index=False)
    print("Done.")

if __name__ == "__main__":
    main()
