import pandas as pd
import os

# Define file paths
CSV_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/site_paths.csv"
EXCEL_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/OWUS_australia_fluxtower_updated.xlsx"
OUTPUT_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_modis_igbp_pft.csv"

def main():
    print("Reading CSV file...")
    try:
        # Read CSV file
        df_csv = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df_csv)} rows from CSV.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print("Reading Excel file...")
    try:
        # Read Excel file
        df_excel = pd.read_excel(EXCEL_FILE)
        print(f"Loaded {len(df_excel)} rows from Excel.")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print("Merging data...")
    # Merge on 'original_site' (CSV) and 'site' (Excel)
    # Using specific column names as requested
    
    # We strip whitespace just in case
    df_csv['original_site'] = df_csv['original_site'].astype(str).str.strip()
    df_excel['site'] = df_excel['site'].astype(str).str.strip()

    # Rename Unnamed columns to Descriptions
    df_excel.rename(columns={
        'Unnamed: 6': 'LC_Type1_Desc',
        'Unnamed: 8': 'LC_Type5_Desc'
    }, inplace=True)

    merged_df = pd.merge(
        df_csv, 
        df_excel, 
        left_on='original_site', 
        right_on='site', 
        how='inner' # Use inner join to ensure we only get matching sites
    )
    
    print(f"Merged dataframe has {len(merged_df)} rows.")

    # Select requested columns
    # siteID,original_site,lat,lon from CSV
    # LC_Type1, LC_Type1_Desc, LC_Type5, LC_Type5_Desc from Excel
    
    columns_to_keep = ['siteID', 'original_site', 'lat', 'lon', 'LC_Type1', 'LC_Type1_Desc', 'LC_Type5', 'LC_Type5_Desc']
    
    # Filter columns
    final_df = merged_df[columns_to_keep].copy()
    
    # Rename columns as requested
    final_df.rename(columns={
        'LC_Type1': 'modis_IGBP_code',
        'LC_Type1_Desc': 'modis_IGBP',
        'LC_Type5': 'modis_PFT_code',
        'LC_Type5_Desc': 'modis_PFT'
    }, inplace=True)
    
    print("Saving to output file...")
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved to {OUTPUT_FILE}")
    
    print("\nPreview of output:")
    print(final_df.head())

if __name__ == "__main__":
    main()
