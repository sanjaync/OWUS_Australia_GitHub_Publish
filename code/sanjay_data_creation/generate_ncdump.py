
import csv
import os
import subprocess

# Define paths
base_dir = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
csv_file_path = os.path.join(base_dir, 'site_paths.csv')
output_dir = os.path.join(base_dir, 'ncdump')

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}")

# Read CSV and process each site
print(f"Reading CSV file: {csv_file_path}")
try:
    with open(csv_file_path, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            site_id = row['siteID']
            nc_file_path = row['nc_file_path']

            if not site_id or not nc_file_path:
                print(f"Skipping row with missing data: {row}")
                continue

            # Verify if netCDF file exists
            if not os.path.exists(nc_file_path):
                print(f"Warning: NetCDF file not found for {site_id}: {nc_file_path}")
                # We might want to save an error message to the output file or just skip
                # Let's write an error message to the output file so the user knows
                output_file_path = os.path.join(output_dir, f"{site_id}_error.txt")
                with open(output_file_path, 'w') as f:
                    f.write(f"File not found: {nc_file_path}\n")
                continue

            print(f"Processing {site_id}...")
            
            # Run ncdump -h
            try:
                result = subprocess.run(['ncdump', '-h', nc_file_path], capture_output=True, text=True, check=True)
                output_content = result.stdout
                
                # Save to file
                output_file_path = os.path.join(output_dir, f"{site_id}.txt")
                with open(output_file_path, 'w') as f:
                    f.write(output_content)
                print(f"  Saved ncdump to {output_file_path}")

            except subprocess.CalledProcessError as e:
                print(f"  Error running ncdump for {site_id}: {e}")
                output_file_path = os.path.join(output_dir, f"{site_id}_error.txt")
                with open(output_file_path, 'w') as f:
                    f.write(f"Error running ncdump: {e}\n")
                    f.write(f"Stderr: {e.stderr}\n")
            except FileNotFoundError:
                 print("  Error: ncdump command not found. Please ensure NetCDF binaries are installed and in PATH.")
                 break

    print("Processing complete.")

except FileNotFoundError:
    print(f"Error: CSV file not found at {csv_file_path}")
