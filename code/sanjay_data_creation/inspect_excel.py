import pandas as pd

EXCEL_FILE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia/sanjay data creation/OWUS_australia_fluxtower_updated.xlsx"

try:
    df = pd.read_excel(EXCEL_FILE)
    print("Columns found in Excel file:")
    print(df.columns.tolist())
    
    print("\nInspecting LC_Type related columns:")
    cols_to_inspect = ['LC_Type1', 'Unnamed: 6', 'LC_Type5', 'Unnamed: 8']
    # Check if they exist first to avoid error if names changed (unlikely but safe)
    existing_cols = [c for c in cols_to_inspect if c in df.columns]
    print(df[existing_cols].head())
except Exception as e:
    print(f"Error reading Excel file: {e}")
