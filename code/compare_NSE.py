import pandas as pd
import os

# Paths to the combined results
new_results_path = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_ensemble_top5/output_corrected/combined/results_bf__ozflux_1.csv'
old_results_path = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_2/output_corrected/combined/results_bf__ozflux_1.csv'

if not os.path.exists(new_results_path):
    print(f"Error: New results not found at {new_results_path}")
    exit(1)
if not os.path.exists(old_results_path):
    print(f"Error: Old results not found at {old_results_path}")
    exit(1)

# Load data
df_new = pd.read_csv(new_results_path)
df_old = pd.read_csv(old_results_path)

# Cleanup column names (some CSVs have leading empty column)
if 'siteID' not in df_new.columns and ',' in df_new.columns[0]:
    df_new = df_new.rename(columns={df_new.columns[0]: 'idx'})
if 'siteID' not in df_old.columns and ',' in df_old.columns[0]:
    df_old = df_old.rename(columns={df_old.columns[0]: 'idx'})

# Merge on siteID
comparison = pd.merge(
    df_old[['siteID', 'NSE', 'Eo']], 
    df_new[['siteID', 'NSE', 'Eo']], 
    on='siteID', 
    suffixes=('_PT', '_Ensemble')
)

comparison['NSE_Diff'] = comparison['NSE_Ensemble'] - comparison['NSE_PT']

# Sort by improvement
comparison = comparison.sort_values(by='NSE_Diff', ascending=False)

print("# Comparison: Priestley-Taylor (PT) vs Ensemble Top 5 Mean PET")
print(comparison[['siteID', 'Eo_PT', 'Eo_Ensemble', 'NSE_PT', 'NSE_Ensemble', 'NSE_Diff']])

# Calculate summary metrics
mean_improvement = comparison['NSE_Diff'].mean()
sites_improved = (comparison['NSE_Diff'] > 0).sum()
total_sites = len(comparison)

print(f"\n## Summary")
print(f"- Sites improved: {sites_improved} / {total_sites} ({sites_improved/total_sites:.1%})")
print(f"- Mean NSE Change: {mean_improvement:.4f}")

output_csv = 'nse_comparison_report.csv'
comparison.to_csv(output_csv, index=False)
print(f"\nResults saved to {output_csv}")
