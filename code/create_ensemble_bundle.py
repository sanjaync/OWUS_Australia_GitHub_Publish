import os
import shutil
import pandas as pd

# List of the 17 sites used in the final v2 paper figures
SELECTED_SITES = [
    'AU-Adr', 'AU-Alp', 'AU-Ctr', 'AU-DaP', 'AU-Eme', 
    'AU-Fog', 'AU-Gat', 'AU-Gre', 'AU-Lit', 'AU-RDF', 
    'AU-Rgf', 'AU-SiP', 'AU-Stp', 'AU-Wal', 'AU-Whr', 
    'AU-YarI', 'AU-Ync'
]

BASE_DIR = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_ensemble_top5'
OUT_DIR = os.path.join(BASE_DIR, 'FINAL_PAPER_BUNDLE_ENSEMBLE')

# Maintain exact structure of output_corrected
dirs_to_make = [
    '01_Main_Paper_Figures',
    '02_Validation_Plots',
    '03_Growing_Seasons',
    'output_corrected/bf/figs/_ozflux_1',
    'output_corrected/bf/files/_ozflux_1',
    'output_corrected/opt/figs/_ozflux_1',
    'output_corrected/opt/files/_ozflux_1',
    'output_corrected/combined'
]

for d in dirs_to_make:
    os.makedirs(os.path.join(OUT_DIR, d), exist_ok=True)
print("Created FINAL_PAPER_BUNDLE_ENSEMBLE directories.")

# 1. Main Paper Figures (From v2 and v1)
src_v2 = os.path.join(BASE_DIR, 'plots_corrected_excluded_sites_v2', 'paper_figures')
if os.path.exists(src_v2):
    for f in os.listdir(src_v2):
        if f.endswith(('.png', '.pdf', '.svg', '.csv')):
            shutil.copy2(os.path.join(src_v2, f), os.path.join(OUT_DIR, '01_Main_Paper_Figures', f))

src_v1 = os.path.join(BASE_DIR, 'plots_corrected_excluded_sites', 'paper_figures')
if os.path.exists(src_v1):
    for f in os.listdir(src_v1):
        if f.endswith(('.png', '.pdf', '.svg', '.csv')):
            dest_file = os.path.join(OUT_DIR, '01_Main_Paper_Figures', f)
            if not os.path.exists(dest_file):
                shutil.copy2(os.path.join(src_v1, f), dest_file)
print("Copied Main Paper Figures (from v1 and v2).")

# 2. Validation Plots (From v2 and v1)
src_apd = os.path.join(BASE_DIR, 'plots_corrected_excluded_sites_v2', 'validation_apd_full')
if os.path.exists(src_apd):
    for f in os.listdir(src_apd):
        if os.path.isfile(os.path.join(src_apd, f)):
            shutil.copy2(os.path.join(src_apd, f), os.path.join(OUT_DIR, '02_Validation_Plots', f))

src_refine = os.path.join(BASE_DIR, 'plots_corrected_excluded_sites', 'validation_refinement')
if os.path.exists(src_refine):
    for f in os.listdir(src_refine):
        if os.path.isfile(os.path.join(src_refine, f)):
            shutil.copy2(os.path.join(src_refine, f), os.path.join(OUT_DIR, '02_Validation_Plots', f))

for txt_file in ['validation_output.txt', 'Scientific_vs_Failed_Comparison.csv']:
    src_txt = os.path.join(BASE_DIR, txt_file)
    if os.path.exists(src_txt):
        shutil.copy2(src_txt, os.path.join(OUT_DIR, '02_Validation_Plots', txt_file))

val_data_dir = os.path.join(BASE_DIR, 'validation_data')
dest_val_data = os.path.join(OUT_DIR, '02_Validation_Plots', 'validation_data')
if os.path.exists(val_data_dir) and not os.path.exists(dest_val_data):
    shutil.copytree(val_data_dir, dest_val_data)
print("Copied Validation Plots and Data.")

# 3. Growing Season Plots (From v1)
src_gs = os.path.join(BASE_DIR, 'plots_corrected_excluded_sites', 'growing_seasons')
if os.path.exists(src_gs):
    for f in os.listdir(src_gs):
        if any(f.startswith(site + '_') for site in SELECTED_SITES):
            shutil.copy2(os.path.join(src_gs, f), os.path.join(OUT_DIR, '03_Growing_Seasons', f))
print("Copied Growing Season Plots.")

# 4. output_corrected/combined -> CSVs
csv_files = [
    ('output_corrected/combined/results_bf__ozflux_1.csv', 'results_bf__ozflux_1.csv'),
    ('output_corrected/combined/results_opt__ozflux_1.csv', 'results_opt__ozflux_1.csv'),
    ('output_corrected/combined/NSE_Comparison_Table_Scientific.csv', 'NSE_Comparison_Table_Scientific.csv'),
    ('nse_comparison_report.csv', 'nse_comparison_report_filtered.csv') # Pulling top-level Ensemble report too
]

for in_csv, out_csv in csv_files:
    in_path = os.path.join(BASE_DIR, in_csv)
    if os.path.exists(in_path):
        df = pd.read_csv(in_path)
        site_col = 'siteID' if 'siteID' in df.columns else ('Site' if 'Site' in df.columns else None)
        if site_col:
            df_filtered = df[df[site_col].isin(SELECTED_SITES)]
            df_filtered.to_csv(os.path.join(OUT_DIR, 'output_corrected/combined', out_csv), index=False)
        else:
            shutil.copy2(in_path, os.path.join(OUT_DIR, 'output_corrected/combined', out_csv))
print("Copied and filtered Data CSVs into output_corrected/combined.")

# 5. output_corrected/bf and output_corrected/opt (figs & files)
for criteria in ['bf', 'opt']:
    fig_src = os.path.join(BASE_DIR, f'output_corrected/{criteria}/figs/_ozflux_1')
    fig_dest = os.path.join(OUT_DIR, f'output_corrected/{criteria}/figs/_ozflux_1')
    if os.path.exists(fig_src):
        for f in os.listdir(fig_src):
            if any(f.startswith(site + '_') for site in SELECTED_SITES):
                shutil.copy2(os.path.join(fig_src, f), os.path.join(fig_dest, f))
    
    pkl_src = os.path.join(BASE_DIR, f'output_corrected/{criteria}/files/_ozflux_1')
    pkl_dest = os.path.join(OUT_DIR, f'output_corrected/{criteria}/files/_ozflux_1')
    if os.path.exists(pkl_src):
        for site in SELECTED_SITES:
            pkl_file = f"{site}.pickle"
            if os.path.exists(os.path.join(pkl_src, pkl_file)):
                shutil.copy2(os.path.join(pkl_src, pkl_file), os.path.join(pkl_dest, pkl_file))

print("Copied MCMC Site Plots and Pickles into output_corrected/bf and opt.")
print(f"\nSUCCESS! All ensemble paper materials bundled to: {OUT_DIR}")
