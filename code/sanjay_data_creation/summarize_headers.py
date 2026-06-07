
import os
import glob

target_dir = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation'
output_file = os.path.join(target_dir, 'csv_headers_summary.txt')

csv_files = glob.glob(os.path.join(target_dir, '*.csv'))
csv_files.sort()

print(f"Found {len(csv_files)} CSV files.")

with open(output_file, 'w') as out_f:
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        try:
            with open(csv_file, 'r') as f:
                header = f.readline().strip()
            out_f.write(f"{filename}\n")
            out_f.write(f"{header}\n")
            out_f.write("-" * 50 + "\n")
            print(f"Processed: {filename}")
        except Exception as e:
            error_msg = f"Error reading {filename}: {str(e)}"
            out_f.write(f"{filename}\n")
            out_f.write(f"{error_msg}\n")
            out_f.write("-" * 50 + "\n")
            print(error_msg)

print(f"Summary written to: {output_file}")
