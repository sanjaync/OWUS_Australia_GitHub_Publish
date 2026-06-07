import pandas as pd
import os

# 1. Setup Paths
input_dir = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation"
output_dir = os.path.join(input_dir, "master_files")

# Safety: Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

files = {
    "paths":        os.path.join(input_dir, "site_paths.csv"),
    "pft":          os.path.join(input_dir, "ozflux_pft.csv"),
    "soil":         os.path.join(input_dir, "ozflux_soil_texture_soil_sensor.csv"),
    "metadata":     os.path.join(input_dir, "ozflux_metadata.csv"),
    "modis_clim":   os.path.join(input_dir, "ozflux_modis_climatology.csv"),
    "veg_frac":     os.path.join(input_dir, "ozflux_vegetation_fraction.csv")
}

# 2. Load Base DataFrame (site_paths.csv)
print("Loading base file (site_paths)...")
master_df = pd.read_csv(files["paths"])

# 3. Define the specific columns to extract
merge_jobs = [
    {
        "name": "pft",
        "path": files["pft"],
        "cols": ["Climate", "pft_0", "pft", "IGBP"],
        "rename": {"Climate": "climate"}
    },
    {
        "name": "soil",
        "path": files["soil"],
        "cols": ["soil_tex_id", "Soil_TEX", "swc_i", "Zm"],
        "rename": {}
    },
    {
        "name": "metadata",
        "path": files["metadata"],
        "cols": ["flux_data_starts", "flux_data_ends"],
        "rename": {}
    },
    {
        "name": "modis_clim",
        "path": files["modis_clim"],
        "cols": ["lai_fpar_file_path"],
        "rename": {}
    },
    {
        "name": "veg_frac",
        "path": files["veg_frac"],
        # We load the raw columns temporarily to calculate fractions
        "cols": ["Percent_NonTree_Vegetation", "Percent_NonVegetated", "Percent_Tree_Cover"],
        "rename": {}
    }
]

# 4. Execute Merges
for job in merge_jobs:
    print(f"Processing {job['name']}...")
    try:
        df_temp = pd.read_csv(job['path'])
        
        # --- ROBUST VEG_FRAC HANDLING ---
        if job['name'] == 'veg_frac':
            print("  > Calculating robust fractional cover (clipped 0-1)...")
            
            # Clip ensures we don't get -0.01 or 1.01 from MODIS noise
            df_temp["frac_T"] = (df_temp["Percent_Tree_Cover"] / 100).clip(0, 1)
            df_temp["frac_H"] = (df_temp["Percent_NonTree_Vegetation"] / 100).clip(0, 1)
            df_temp["frac_B"] = (df_temp["Percent_NonVegetated"] / 100).clip(0, 1)
            
            # OWUS Logic: frac_V is 1 - Bare Ground
            df_temp["frac_V"] = (1 - df_temp["frac_B"]).clip(0, 1)
            
            # QC Check: Sum of components (T + H + B) should be ~1.0
            df_temp["frac_sum"] = df_temp["frac_T"] + df_temp["frac_H"] + df_temp["frac_B"]
            
            # Define columns to keep (including sum for validation)
            cols_to_keep = ["siteID", "frac_V", "frac_T", "frac_H", "frac_B", "frac_sum"]
            
        else:
            # Standard handling for other files
            cols_to_keep = ["siteID"] + job['cols']
            
        # --- STANDARD MERGE LOGIC ---
        
        # Check available columns
        available_cols = [c for c in cols_to_keep if c in df_temp.columns]
        df_subset = df_temp[available_cols].copy()
        
        # Rename if needed
        if job['rename']:
            df_subset.rename(columns=job['rename'], inplace=True)
        
        # Left Merge
        master_df = pd.merge(master_df, df_subset, on="siteID", how="left")
        
    except FileNotFoundError:
        print(f"  ERROR: File not found: {job['path']}")
    except Exception as e:
        print(f"  ERROR processing {job['name']}: {e}")

# 5. Reorder Columns
desired_order = [
    "siteID", "original_site", "lat", "lon", 
    "climate", "pft_0", "pft", "IGBP", 
    "soil_tex_id", "Soil_TEX", "swc_i", "Zm", 
    "flux_data_starts", "flux_data_ends", 
    "nc_file_path", "lai_fpar_file_path",
    # Calculated columns
    "frac_V", "frac_T", "frac_H", "frac_B", "frac_sum"
]

# Filter to keep only columns that exist
final_cols = [c for c in desired_order if c in master_df.columns]
master_df = master_df[final_cols]

# 6. Save to new directory
output_file = os.path.join(output_dir, "ozflux_MASTER_dataset.csv")
master_df.to_csv(output_file, index=False)

print("-" * 30)
print(f"SUCCESS! Master file created at:\n{output_file}")
print("-" * 30)

# 7. Quick Validation Report for You
if "frac_sum" in master_df.columns:
    print("\n[VALIDATION REPORT]")
    print(master_df[["frac_T", "frac_H", "frac_B", "frac_sum"]].describe())
    print("\nCheck 'frac_sum' above. Mean should be very close to 1.0.")