import pandas as pd
import os

base_dir = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/FINAL_PAPER_BUNDLE/01_Main_Paper_Figures"
ens_dir = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_ensemble_top5/FINAL_PAPER_BUNDLE_ENSEMBLE/01_Main_Paper_Figures"

files = [
    "4_results_comparison_metrics_stats.csv",
    "4_sm_gof_stats.csv",
    "5_flux_scatter_stats.csv",
    "SI_piRpiF_stats.csv"
]

print("=== STATS COMPARISON ===")
for f in files:
    bf_path = os.path.join(base_dir, f)
    ens_path = os.path.join(ens_dir, f)
    
    if os.path.exists(bf_path) and os.path.exists(ens_path):
        print(f"\n--- {f} ---")
        try:
            df_b = pd.read_csv(bf_path)
            df_e = pd.read_csv(ens_path)
            
            # Print merged side by side
            for col in df_b.columns:
                if col not in ['Variable', 'Label', 'Metric']:
                    # Try to merge or just print
                    pass
                    
            if 'Variable' in df_b.columns:
                merged = pd.merge(df_b, df_e, on=['Variable', 'Label'], suffixes=('_Base', '_Ens'))
                for _, row in merged.iterrows():
                    print(f"\n{row['Variable']}:")
                    for c in df_b.columns:
                        if c not in ['Variable', 'Label']:
                            print(f"  {c}: Base={row[c+'_Base']:.4f}, Ens={row[c+'_Ens']:.4f} (Diff: {row[c+'_Ens'] - row[c+'_Base']:.4f})")
            else:
                # No variable column, just row by row
                for i in range(len(df_b)):
                    print(f"\nRow {i}:")
                    for c in df_b.columns:
                        try:
                            diff = float(df_e.iloc[i][c]) - float(df_b.iloc[i][c])
                            print(f"  {c}: Base={df_b.iloc[i][c]:.4f}, Ens={df_e.iloc[i][c]:.4f} (Diff: {diff:.4f})")
                        except:
                            print(f"  {c}: Base={df_b.iloc[i][c]}, Ens={df_e.iloc[i][c]}")
        except Exception as e:
            print("Error processing:", e)
