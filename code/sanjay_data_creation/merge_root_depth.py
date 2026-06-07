import csv
import os

# Source File 1: Site Paths
SITE_PATHS_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/site_paths.csv"

# Source File 2: Root Depth
# Note: User provided /fs04/scratch2/... path, but I will check if it maps to /home/sanjays/et97_scratch2/...
# However, `ls` confirmed the absolute path provided by user exists.
ROOT_DEPTH_FILE = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/rootdepth_paper/OzFlux_RootDepth_Final_FocalFill.csv"

# Output File
OUTPUT_FILE = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/ozflux_rootdepth_paper.csv"
# Assuming write access to the same directory

def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f: # utf-8-sig to handle BOM if present
        reader = csv.DictReader(f)
        return list(reader)

def main():
    sites_data = read_csv(SITE_PATHS_FILE)
    root_data = read_csv(ROOT_DEPTH_FILE)

    # Create lookup map for root depth by site
    # Source file column "site", target value column "first"
    root_map = {}
    for row in root_data:
        site_name = row.get("site")
        root_val = row.get("first")
        if site_name:
            root_map[site_name] = root_val

    # Prepare output rows
    output_rows = []
    # Columns: siteID,original_site,lat,lon,root_depth_from_paper
    
    for row in sites_data:
        orig_site = row["original_site"]
        
        # Get root depth, default to empty or keep it if missing? 
        # User didn't specify behavior for missing data, but usually we just leave it empty or report warning.
        root_depth = root_map.get(orig_site, "")
        
        if not root_depth:
            print(f"Warning: No match for site '{orig_site}' in root depth file.")

        output_rows.append({
            "siteID": row["siteID"],
            "original_site": orig_site,
            "lat": row["lat"],
            "lon": row["lon"],
            "root_depth_from_paper": root_depth
        })

    # Write output
    fieldnames = ["siteID", "original_site", "lat", "lon", "root_depth_from_paper"]
    
    # Ensure directory exists (though it should as file 1 is in it)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
        
    print(f"Successfully created {OUTPUT_FILE} with {len(output_rows)} rows.")

if __name__ == "__main__":
    main()
