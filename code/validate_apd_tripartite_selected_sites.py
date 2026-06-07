#!/usr/bin/env python3
"""
validate_apd_tripartite_selected_sites.py
------------------------------------------
Tripartite Continental Validation (BF vs Optimised vs APD benchmarks)
restricted to a hand-selected list of 17 sites.

Output goes to:
  plots_corrected_excluded_sites_v2/validation_apd_full/
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set plotting style
sns.set_theme(style="whitegrid")
plt.switch_backend('Agg')

# ─────────────────────────────────────────────────────────────────────────────
#  SITES TO INCLUDE
# ─────────────────────────────────────────────────────────────────────────────
SELECTED_SITES = [
    'AU-Adr',
    'AU-Alp',
    'AU-Ctr',
    'AU-DaP',
    'AU-Eme',
    'AU-Fog',
    'AU-Gat',
    'AU-Gre',
    'AU-Lit',
    'AU-RDF',
    'AU-Rgf',
    'AU-SiP',
    'AU-Stp',
    'AU-Wal',
    'AU-Whr',
    'AU-YarI',
    'AU-Ync',
]

# ─────────────────────────────────────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────────────────────────────────────
RESULT_OPT_PATH    = 'output_corrected/combined/results_opt__ozflux_1.csv'
RESULT_BF_PATH     = 'output_corrected/combined/results_bf__ozflux_1.csv'
PFT_PATH           = 'sanjay data creation/ozflux_pft.csv'
APD_BENCHMARK_PATH = 'sanjay data creation/Austraits_data_processed/audit/selected_pft_params_refs_from_austraits_FULL_LONG.csv'
OUTPUT_DIR         = 'plots_corrected_excluded_sites_v2/validation_apd_full'

os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_tripartite_validation():
    print("--- Tripartite Continental Validation (BF vs Optimized vs APD) ---")
    print(f"    Restricted to {len(SELECTED_SITES)} selected sites")
    print(f"    Output: {OUTPUT_DIR}\n")

    # 1. Load optimized results
    res_opt = pd.read_csv(RESULT_OPT_PATH)
    res_opt.columns = [c.strip().lower() for c in res_opt.columns]

    # 2. Load Bayesian Fit (Baseline) results
    res_bf = pd.read_csv(RESULT_BF_PATH)
    res_bf.columns = [c.strip().lower() for c in res_bf.columns]

    # 3. Load PFT mapping
    pft_map = pd.read_csv(PFT_PATH)
    pft_map.columns = [c.strip().lower() for c in pft_map.columns]
    site_to_pft = dict(zip(pft_map['siteid'], pft_map['pft']))

    # 4. Load APD Benchmarks
    apd = pd.read_csv(APD_BENCHMARK_PATH)

    # Restrict to selected sites (lowercase comparison)
    selected_lower = [s.lower() for s in SELECTED_SITES]

    # Traits to compare
    traits_to_compare = {
        'kl_max': 'sapwood_specific_hydraulic_conductivity',
        'px50':   'stem_water_potential_50percent_lost_conductivity',
        'pg50':   'leaf_water_potential_50percent_lost_conductivity',
        'g_max':  'leaf_stomatal_conductance_per_area_at_Amax',
    }

    comparison_data = []

    for owus_p, apd_t in traits_to_compare.items():
        print(f"Processing trait: {owus_p} ...")
        apd_trait = apd[apd['trait_name'] == apd_t]

        # Only iterate over selected sites that exist in opt results
        available_sites = [s for s in res_opt['siteid'].unique()
                           if s.lower() in selected_lower]
        missing = set(SELECTED_SITES) - {s for s in res_opt['siteid'].unique()
                                          if s.lower() in selected_lower}
        if missing:
            print(f"  WARNING: not found in opt CSV: {sorted(missing)}")

        for sid in available_sites:
            site_pft = site_to_pft.get(sid)
            if not site_pft:
                print(f"  WARNING: no PFT mapping for {sid}, skipping.")
                continue

            benchmark_row = apd_trait[apd_trait['PFT'] == site_pft]
            if benchmark_row.empty:
                print(f"  WARNING: no APD benchmark for {sid} (PFT={site_pft}), skipping.")
                continue

            benchmark_val = benchmark_row.iloc[0]['value_median']

            # Get Optimized Value (Mean)
            row_opt = res_opt[res_opt['siteid'] == sid].iloc[0]
            opt_val = np.nan
            for col in [f'{owus_p}_mean', owus_p]:
                if col in row_opt and not pd.isna(row_opt[col]):
                    opt_val = row_opt[col]
                    break

            # Get BF (Baseline) Value
            row_bf = res_bf[res_bf['siteid'] == sid]
            bf_val = np.nan
            if not row_bf.empty:
                row_bf_val = row_bf.iloc[0]
                bf_val = row_bf_val.get(owus_p, np.nan)

            if not pd.isna(opt_val) or not pd.isna(bf_val):
                comparison_data.append({
                    'siteID':         sid,
                    'PFT':            site_pft,
                    'Trait':          owus_p,
                    'APD_Benchmark':  benchmark_val,
                    'Optimized_Mean': opt_val,
                    'BF_Baseline':    bf_val,
                })

    df_comp = pd.DataFrame(comparison_data)

    if df_comp.empty:
        print("ERROR: No comparison data generated. Check paths and site IDs.")
        return

    print(f"\nTotal records: {len(df_comp)} across "
          f"{df_comp['siteID'].nunique()} sites and "
          f"{df_comp['Trait'].nunique()} traits.")

    # ── Plotting ──────────────────────────────────────────────────────────────
    for trait in df_comp['Trait'].unique():
        trait_df = df_comp[df_comp['Trait'] == trait]
        plt.figure(figsize=(14, 10))

        # Optimized as circles
        sns.scatterplot(data=trait_df, x='APD_Benchmark', y='Optimized_Mean',
                        color='salmon', s=150, label='Optimized (Mean)',
                        marker='o', alpha=0.9)

        # BF Baseline as squares
        sns.scatterplot(data=trait_df, x='APD_Benchmark', y='BF_Baseline',
                        color='gray', s=100, label='BF (Baseline)',
                        marker='s', alpha=0.6)

        # Labels and arrows
        for _, row in trait_df.iterrows():
            plt.text(row['APD_Benchmark'], row['Optimized_Mean'],
                     f" {row['siteID']}", fontsize=9,
                     verticalalignment='bottom', alpha=0.8)
            if not pd.isna(row['BF_Baseline']) and not pd.isna(row['Optimized_Mean']):
                plt.annotate('',
                             xy=(row['APD_Benchmark'], row['Optimized_Mean']),
                             xytext=(row['APD_Benchmark'], row['BF_Baseline']),
                             arrowprops=dict(arrowstyle='->', color='blue',
                                             alpha=0.3, lw=0.5))

        # 1:1 line
        all_y = np.concatenate([trait_df['Optimized_Mean'].dropna(),
                                 trait_df['BF_Baseline'].dropna()])
        all_x = trait_df['APD_Benchmark'].dropna()
        if len(all_x) > 0 and len(all_y) > 0:
            min_v = min(all_x.min(), all_y.min())
            max_v = max(all_x.max(), all_y.max())
            plt.plot([min_v, max_v], [min_v, max_v], 'k--', alpha=0.5,
                     label='1:1 Line')

        plt.title(
            f"Continental Tri-Validation: {trait}\n"
            f"(Optimized vs Baseline vs APD Benchmarks) — {len(trait_df)} sites",
            fontsize=16)
        plt.xlabel("APD Benchmark (PFT Median)", fontsize=14)
        plt.ylabel("Model Trait Prediction (Optimized & Baseline)", fontsize=14)
        plt.legend(loc='best')
        plt.tight_layout()

        out_path = os.path.join(OUTPUT_DIR, f"{trait}_Tri_Scatter_APD.png")
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"  Saved: {out_path}")

    # ── Save summary CSV ───────────────────────────────────────────────────────
    csv_path = os.path.join(OUTPUT_DIR, 'apd_tripartite_summary.csv')
    df_comp.to_csv(csv_path, index=False)
    print(f"\nFull results saved to {csv_path}")

    # ── Summary stats ──────────────────────────────────────────────────────────
    summary_stats = []
    for trait in df_comp['Trait'].unique():
        t = df_comp[df_comp['Trait'] == trait]
        bf_rmse  = np.sqrt(((t['BF_Baseline']    - t['APD_Benchmark'])**2).mean())
        opt_rmse = np.sqrt(((t['Optimized_Mean'] - t['APD_Benchmark'])**2).mean())
        summary_stats.append({
            'Trait':           trait,
            'N_sites':         len(t),
            'Baseline_RMSE':   bf_rmse,
            'Optimized_RMSE':  opt_rmse,
            'Improvement_Pct': (bf_rmse - opt_rmse) / bf_rmse * 100
                                if bf_rmse != 0 else 0,
        })

    stats_df = pd.DataFrame(summary_stats)
    stats_path = os.path.join(OUTPUT_DIR, 'apd_validation_summary.csv')
    stats_df.to_csv(stats_path, index=False)
    print("\nQuantitative Improvement Summary:")
    print(stats_df.to_string(index=False))
    print(f"\nSaved to {stats_path}")


if __name__ == "__main__":
    run_tripartite_validation()
