import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

cwd = os.getcwd()

# The original full NSE comparison report
in_csv = os.path.join(cwd, 'nse_comparison_report.csv')
out_dir = os.path.join(cwd, 'FINAL_PAPER_BUNDLE_ENSEMBLE', '01_Main_Paper_Figures')

# Make sure directory exists
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(in_csv)

# Drop the known catastrophic/always-wet sites to leave the true baseline dataset (24 sites)
exclude_list = ['AU-Wal', 'AU-Lox', 'AU-Fog', 'AU-Alp', 'AU-War']
df_clean = df[~df['siteID'].isin(exclude_list)].copy()

# Sort by Baseline PT performance for a smooth visual curve
df_clean = df_clean.sort_values(by='NSE_PT', ascending=True).reset_index(drop=True)

# 1. Output the filtered CSV for the 22 sites
out_csv = os.path.join(out_dir, 'Full_22_Sites_NSE_Comparison.csv')
df_clean.to_csv(out_csv, index=False)
print(f"Saved {len(df_clean)} site comparison data to {out_csv}")

# 2. Generate Wide Bar Chart
x = np.arange(len(df_clean))
width = 0.35

fig, ax = plt.subplots(figsize=(14, 6))

rects1 = ax.bar(x - width/2, df_clean['NSE_PT'], width, label='Priestley-Taylor (Baseline)', color='#4c72b0')
rects2 = ax.bar(x + width/2, df_clean['NSE_Ensemble'], width, label='Ensemble PET', color='#dd8452')

ax.set_ylabel('Nash-Sutcliffe Efficiency (NSE)', fontsize=12)
ax.set_title('Full Dataset Comparison (22 Sites): Priestley-Taylor vs Ensemble PET', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(df_clean['siteID'], rotation=45, ha='right')
ax.legend(fontsize=12)
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Draw a line at NSE=0
ax.axhline(0, color='black', linewidth=1)

fig.tight_layout()
bar_path = os.path.join(out_dir, 'Full_22_Sites_NSE_BarChart.png')
plt.savefig(bar_path, dpi=300)
plt.close()
print(f"Saved Full Bar Chart to {bar_path}")

# 3. Generate Scatter Plot (1:1 line)
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(df_clean['NSE_PT'], df_clean['NSE_Ensemble'], color='#dd8452', s=80, alpha=0.8, edgecolor='black')

# 1:1 line
min_val = min(df_clean['NSE_PT'].min(), df_clean['NSE_Ensemble'].min()) - 0.1
max_val = max(df_clean['NSE_PT'].max(), df_clean['NSE_Ensemble'].max()) + 0.1
ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.6, label='1:1 Line (No Change)')

ax.set_xlabel('NSE (Priestley-Taylor Baseline)', fontsize=12)
ax.set_ylabel('NSE (Ensemble PET)', fontsize=12)
ax.set_title('Ensemble PET Performance Gains', fontsize=14)
ax.grid(linestyle='--', alpha=0.5)
ax.legend(fontsize=12)

# Annotate the big movers (e.g. diff > 0.05 or < -0.05)
for i, row in df_clean.iterrows():
    diff = row['NSE_Ensemble'] - row['NSE_PT']
    if abs(diff) > 0.05:
        ax.annotate(row['siteID'], (row['NSE_PT'], row['NSE_Ensemble']), 
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

fig.tight_layout()
scatter_path = os.path.join(out_dir, 'Full_22_Sites_NSE_Scatter.png')
plt.savefig(scatter_path, dpi=300)
plt.close()
print(f"Saved Full Scatter Plot to {scatter_path}")

print("Done! Both the CSV and 2 plots have been added to your FINAL_PAPER_BUNDLE_ENSEMBLE.")
