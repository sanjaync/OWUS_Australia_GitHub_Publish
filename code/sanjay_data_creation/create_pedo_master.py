import pandas as pd
import os

# Define file paths
pedo_file = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_pedo_transfer_functions.csv"
master_file = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/master_files/ozflux_MASTER_dataset.csv"
output_file = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/master_files/pedo_master_file.csv"

# Load the data
print(f"Loading {pedo_file}...")
df_pedo = pd.read_csv(pedo_file)

print(f"Loading {master_file}...")
df_master = pd.read_csv(master_file)

# Columns to include from pedo file
cols_to_include = ['site', 'MAXSMC', 'DRYSMC', 'BB', 'SATPSI', 'SATDK']
df_pedo_subset = df_pedo[cols_to_include]

# Merge the data
# master['original_site'] matches pedo['site']
print("Merging dataframes...")
merged_df = pd.merge(df_master, df_pedo_subset, left_on='original_site', right_on='site', how='left')

# Drop the redundant 'site' column from the merge if it exists separately
if 'site' in merged_df.columns:
    merged_df = merged_df.drop(columns=['site'])

# Save the result
print(f"Saving to {output_file}...")
merged_df.to_csv(output_file, index=False)

print("Merge complete.")
print(f"Total rows: {len(merged_df)}")
print(f"Columns: {merged_df.columns.tolist()}")
