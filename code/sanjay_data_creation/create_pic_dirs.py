
import csv
import os

base_dir = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
csv_file_path = os.path.join(base_dir, 'site_paths.csv')
pic_base_dir = os.path.join(base_dir, 'pic')

# Create base pic directory
if not os.path.exists(pic_base_dir):
    os.makedirs(pic_base_dir)
    print(f"Created base directory: {pic_base_dir}")

# Read CSV and create subdirectories
print(f"Reading CSV file: {csv_file_path}")
try:
    with open(csv_file_path, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            site_id = row['siteID']
            if not site_id:
                continue
            
            site_dir = os.path.join(pic_base_dir, site_id)
            if not os.path.exists(site_dir):
                os.makedirs(site_dir)
                # print(f"Created directory: {site_dir}")
            count += 1
            
    print(f"Created/Verified directories for {count} sites.")

except FileNotFoundError:
    print(f"Error: CSV file not found at {csv_file_path}")
