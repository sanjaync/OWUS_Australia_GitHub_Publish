#!/usr/bin/env python3
"""
generate_17_sites_ensemble.py
---------------------------------
Re-generate paper figures for the Ensemble PET run using the strict 
17-site curated list, and generate an NSE comparison plot.

Output goes to:
  plots_corrected_excluded_sites_v2/paper_figures/
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

SELECTED_SITES = [
    'AU-Adr', 'AU-Alp', 'AU-Ctr', 'AU-DaP', 'AU-Eme', 
    'AU-Fog', 'AU-Gat', 'AU-Gre', 'AU-Lit', 'AU-RDF', 
    'AU-Rgf', 'AU-SiP', 'AU-Stp', 'AU-Wal', 'AU-Whr', 
    'AU-YarI', 'AU-Ync'
]

# Note: As in create_figs, AU-Wal, AU-Fog, AU-Alp will be dropped during plotting by check_common_sites
# leaving 14 sites in the plots, perfectly mirroring the main scientific paper dataset.

cwd = os.getcwd()

os.environ['WUS_DATA_PATH']       = os.path.join(cwd, 'output_corrected')
os.environ['WUS_INPUT_DATA_PATH'] = os.path.join(cwd, 'input_data')
os.environ['WUS_FIGS_PATH']       = os.path.join(cwd, 'plots_corrected_excluded_sites_v2', 'paper_figures')
os.environ['WUS_SUBPATH_PREFIX']  = '_ozflux_1'

os.makedirs(os.environ['WUS_FIGS_PATH'], exist_ok=True)
print(f"Output directory: {os.environ['WUS_FIGS_PATH']}")

try:
    from create_figs import *
    print("Successfully imported create_figs")
except ImportError as e:
    print(f"Error importing create_figs: {e}")
    sys.exit(1)

def filter_sites(df, sites):
    filtered = df[df['siteID'].isin(sites)].copy()
    found = sorted(filtered['siteID'].tolist())
    print(f"  Sites retained ({len(found)}): {found}")
    return filtered

def plot_nse_comparison(df):
    """Generates a grouped bar chart for NSE_PT vs NSE_Ensemble"""
    print("\n[8/8] Figure: NSE Comparison Bar Chart...")
    try:
        # Filter strictly to the 14 sites that actually make it into the paper figures
        # (Excluding the catastrophic ones so it matches the other plots)
        exclude_list = ['AU-Wal', 'AU-Lox', 'AU-Fog', 'AU-Alp', 'AU-War']
        df_clean = df[~df['siteID'].isin(exclude_list)].copy()
        
        # Sort by NSE_PT to make the graph readable
        df_clean = df_clean.sort_values(by='NSE_PT', ascending=True).reset_index(drop=True)
        
        x = np.arange(len(df_clean))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Use visually appealing colors
        rects1 = ax.bar(x - width/2, df_clean['NSE_PT'], width, label='PT (Baseline)', color='#4c72b0')
        rects2 = ax.bar(x + width/2, df_clean['NSE_Ensemble'], width, label='Ensemble PET', color='#dd8452')

        ax.set_ylabel('Nash-Sutcliffe Efficiency (NSE)', fontsize=12)
        ax.set_title('NSE Comparison: Priestley-Taylor vs Ensemble PET', fontsize=14)
        ax.set_xticks(x)
        ax.set_xticklabels(df_clean['siteID'], rotation=45, ha='right')
        ax.legend(fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        # Draw a line at NSE=0
        ax.axhline(0, color='black', linewidth=1)

        fig.tight_layout()
        save_path = os.path.join(os.environ['WUS_FIGS_PATH'], 'NSE_PT_vs_Ensemble_BarChart.png')
        plt.savefig(save_path, dpi=300)
        plt.close()
        print(f"  Done. Saved to {save_path}")
    except Exception as e:
        print(f"  FAILED: {e}")

def generate_figures():
    print("\n=== Loading result files ===")
    
    # In the ensemble folder, results might be in output/ or output_corrected/
    # Let's check output_corrected first as it's the standard for curated results
    opt_path = os.path.join(os.environ['WUS_DATA_PATH'], 'combined', 'results_opt__ozflux_1.csv')
    bf_path  = os.path.join(os.environ['WUS_DATA_PATH'], 'combined', 'results_bf__ozflux_1.csv')
    nse_comp_path = os.path.join(cwd, 'nse_comparison_report.csv')

    if not os.path.exists(opt_path):
        print(f"ERROR: Optimization results not found at {opt_path}")
        return

    res_opt_full = pd.read_csv(opt_path)
    res_dd_full  = pd.read_csv(bf_path)
    nse_comp_full = pd.read_csv(nse_comp_path) if os.path.exists(nse_comp_path) else None

    print("\n--- Filtering to selected sites (17 sites) ---")
    res_opt = filter_sites(res_opt_full, SELECTED_SITES)
    res_dd  = filter_sites(res_dd_full,  SELECTED_SITES)

    print("\n=== Generating Figures ===")
    print("\n[1/8] Figure 4: All Metrics Scatter...")
    try: scatter_all_metrics(res_opt.copy(), res_dd.copy(), figname='comparison_metrics'); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[2/8] Figure: SM Goodness-of-Fit...")
    try: plot_sm_gof(res_opt.copy(), res_dd.copy(), figname='4_sm_gof'); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[3/8] Figure: Flux Scatter...")
    try: flux_scatter(res_opt.copy(), res_dd.copy(), figname='5_flux_scatter'); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[4/8] Figure: Budyko Aridity...")
    try: wb_aridity(res_opt.copy(), res_dd.copy(), figname='budyko_f'); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[5/8] Figure: Budyko Sigma...")
    try: wb_aridity_sigma(res_opt.copy(), res_dd.copy(), figname='budyko_s'); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[6/8] Figure: ET Partitioning...")
    try: et_part(res_opt.copy()); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    print("\n[7/8] SI Figure: piF vs piR scatter...")
    try: piF_piR_scatter(res_dd.copy(), res_opt.copy()); print("  Done.")
    except Exception as e: print(f"  FAILED: {e}")

    if nse_comp_full is not None:
        nse_filtered = filter_sites(nse_comp_full, SELECTED_SITES)
        plot_nse_comparison(nse_filtered)
    else:
        print("\n[8/8] Skipped NSE Comparison Bar Chart (csv not found).")

    print(f"\n=== All figures written to: {os.environ['WUS_FIGS_PATH']} ===")

if __name__ == "__main__":
    generate_figures()
