import pandas as pd
import os

# Define file paths
CSV_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/site_paths.csv"

CLIM_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/modis_lai_fpar_data/modis_climatology_curves_2003_2025/"
DAILY_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/modis_lai_fpar_data/modis_daily_with_smoothed_curve_2003_2025/"

OUTPUT_CLIM = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_modis_climatology.csv"
OUTPUT_DAILY = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_modis_daily.csv"

def main():
    print("Reading CSV file...")
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Loaded {len(df)} rows from CSV.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Clean site names
    df['original_site'] = df['original_site'].astype(str).str.strip()

    # Create Climatology DataFrame
    print("Creating Climatology CSV...")
    df_clim = df.copy()
    df_clim['lai_fpar_file_path'] = df_clim['original_site'].apply(
        lambda site: os.path.join(CLIM_DIR, f"{site}_MODIS_DOY_climatology_mean_win31_2003_2025.csv")
    )
    
    # Verify file existence (optional but good for logs)
    missing_clim = df_clim[~df_clim['lai_fpar_file_path'].apply(os.path.exists)]
    if not missing_clim.empty:
        print(f"Warning: {len(missing_clim)} climatology files not found on disk.")
        # print(missing_clim['lai_fpar_file_path'].tolist()) # verbose
    else:
        print("All climatology files found.")

    # Select columns
    cols = ['siteID', 'original_site', 'lat', 'lon', 'lai_fpar_file_path']
    df_clim = df_clim[cols]
    df_clim.to_csv(OUTPUT_CLIM, index=False)
    print(f"Saved to {OUTPUT_CLIM}")

    # Create Daily DataFrame
    print("Creating Daily CSV...")
    df_daily = df.copy()
    df_daily['lai_fpar_file_path'] = df_daily['original_site'].apply(
        lambda site: os.path.join(DAILY_DIR, f"{site}_MODIS_DAILY_with_smoothed_curve_mean_win31_2003_2025.csv")
    )

    # Verify file existence
    missing_daily = df_daily[~df_daily['lai_fpar_file_path'].apply(os.path.exists)]
    if not missing_daily.empty:
        print(f"Warning: {len(missing_daily)} daily files not found on disk.")
    else:
        print("All daily files found.")

    df_daily = df_daily[cols]
    df_daily.to_csv(OUTPUT_DAILY, index=False)
    print(f"Saved to {OUTPUT_DAILY}")

if __name__ == "__main__":
    main()
