import pandas as pd
import os

# Define file paths
CSV_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/site_paths.csv"
EXCEL_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/OWUS_australia_fluxtower_updated.xlsx"
ROOT_DEPTH_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/rootdepth_paper/OzFlux_RootDepth_Final_FocalFill.csv"
OUTPUT_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_metadata.csv"

def main():
    print("Reading CSV file...")
    try:
        df_csv = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df_csv)} rows from CSV.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print("Reading Excel file...")
    try:
        df_excel = pd.read_excel(EXCEL_FILE)
        print(f"Loaded {len(df_excel)} rows from Excel.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print("Reading Root Depth file...")
    try:
        df_root = pd.read_csv(ROOT_DEPTH_FILE)
        print(f"Loaded {len(df_root)} rows from Root Depth CSV.")
    except Exception as e:
        print(f"Error reading Root Depth file: {e}")
        return

    print("Merging data...")
    # Clean keys
    df_csv['original_site'] = df_csv['original_site'].astype(str).str.strip()
    df_excel['site'] = df_excel['site'].astype(str).str.strip()
    df_root['site'] = df_root['site'].astype(str).str.strip()

    # Merge 1: CSV + Excel
    merged_df = pd.merge(
        df_csv, 
        df_excel, 
        left_on='original_site', 
        right_on='site', 
        how='inner'
    )
    print(f"Merged CSV+Excel has {len(merged_df)} rows.")

    # Merge 2: Result + Root Depth
    # Note: Root depth file might have duplicates or missing sites, we'll use left join to keep all sites we have so far?
    # Or inner if we only want sites present in all? 
    # User instruction: "match site with original_site"
    # Assuming we want to keep the sites we have already, so default to left join or inner join depending on strictness.
    # Given previous steps used inner join, let's stick to inner to ensure data quality, OR left if we want to preserve partial data.
    # However, usually metadata files want complete rows. Let's use inner join to be safe, but check if we lose rows.
    # Actually, if we use inner join we might lose sites if they are not in root depth file.
    # Let's check overlap.
    
    # We will use left join onto the existing merged_df to preserve the 34 sites we have.
    # If root depth file is missing a site, it will have NaN dates, which is better than dropping the site.
    
    merged_final = pd.merge(
        merged_df,
        df_root[['site', 'start', 'end']], # Only take needed columns to avoid collisions
        left_on='original_site',
        right_on='site',
        how='left',
        suffixes=('', '_root')
    )
    
    print(f"Final merged dataframe has {len(merged_final)} rows.")

    # Rename columns
    merged_final.rename(columns={
        'start': 'flux_data_starts',
        'end': 'flux_data_ends'
    }, inplace=True)

    # Select columns
    columns_to_keep = [
        'siteID', 
        'original_site', 
        'lat', 
        'lon', 
        'Vegetation Type', 
        'Soil Type', 
        'Altitude_m', 
        'Tower_Height_m', 
        'Canopy_Height_m',
        'flux_data_starts',
        'flux_data_ends'
    ]
    
    final_df = merged_final[columns_to_keep]
    
    print("Saving to output file...")
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved to {OUTPUT_FILE}")
    
    print("\nPreview of output:")
    print(final_df.head())

if __name__ == "__main__":
    main()
