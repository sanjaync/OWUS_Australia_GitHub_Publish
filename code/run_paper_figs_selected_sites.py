#!/usr/bin/env python3
"""
run_paper_figs_selected_sites.py
---------------------------------
Re-generate paper figures using data from output_corrected/ and
restricting to a hand-selected list of sites.

Output goes to:
  plots_corrected_excluded_sites_v2/paper_figures/
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

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
#  ENVIRONMENT SETUP  (must be done BEFORE importing create_figs)
# ─────────────────────────────────────────────────────────────────────────────
cwd = os.getcwd()

os.environ['WUS_DATA_PATH']       = os.path.join(cwd, 'output_corrected')
os.environ['WUS_INPUT_DATA_PATH'] = os.path.join(cwd, 'input_data')
os.environ['WUS_FIGS_PATH']       = os.path.join(cwd, 'plots_corrected_excluded_sites_v2', 'paper_figures')
os.environ['WUS_SUBPATH_PREFIX']  = '_ozflux_1'

# Create output directory
os.makedirs(os.environ['WUS_FIGS_PATH'], exist_ok=True)
print(f"Output directory: {os.environ['WUS_FIGS_PATH']}")

# ─────────────────────────────────────────────────────────────────────────────
#  IMPORT FIGURE-GENERATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
try:
    from create_figs import *
    print("Successfully imported create_figs")
except ImportError as e:
    print(f"Error importing create_figs: {e}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def filter_sites(df, sites):
    """Return rows where siteID is in the given list."""
    filtered = df[df['siteID'].isin(sites)].copy()
    missing = set(sites) - set(filtered['siteID'].tolist())
    if missing:
        print(f"  WARNING: these sites were not found in the CSV: {sorted(missing)}")
    found = sorted(filtered['siteID'].tolist())
    print(f"  Sites retained ({len(found)}): {found}")
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def generate_figures():
    print("\n=== Loading result files ===")

    opt_path = os.path.join(os.environ['WUS_DATA_PATH'], 'combined', 'results_opt__ozflux_1.csv')
    bf_path  = os.path.join(os.environ['WUS_DATA_PATH'], 'combined', 'results_bf__ozflux_1.csv')

    if not os.path.exists(opt_path):
        print(f"ERROR: Optimization results not found at {opt_path}")
        return
    if not os.path.exists(bf_path):
        print(f"ERROR: Data-driven results not found at {bf_path}")
        return

    res_opt_full = pd.read_csv(opt_path)
    res_dd_full  = pd.read_csv(bf_path)

    print(f"  opt CSV: {len(res_opt_full)} sites total")
    print(f"  bf  CSV: {len(res_dd_full)} sites total")

    print("\n--- Filtering to selected sites ---")
    print("opt:")
    res_opt = filter_sites(res_opt_full, SELECTED_SITES)
    print("bf:")
    res_dd  = filter_sites(res_dd_full,  SELECTED_SITES)

    # ── Figure generation ──────────────────────────────────────────────────
    print("\n=== Generating Figures ===")

    print("\n[1/7] Figure 4: All Metrics Scatter (4_results_comparison_metrics) ...")
    try:
        scatter_all_metrics(res_opt.copy(), res_dd.copy(), figname='comparison_metrics')
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[2/7] Figure: SM Goodness-of-Fit (4_sm_gof) ...")
    try:
        plot_sm_gof(res_opt.copy(), res_dd.copy(), figname='4_sm_gof')
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[3/7] Figure: Flux Scatter (5_flux_scatter) ...")
    try:
        flux_scatter(res_opt.copy(), res_dd.copy(), figname='5_flux_scatter')
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[4/7] Figure: Budyko Aridity (budyko_f) ...")
    try:
        wb_aridity(res_opt.copy(), res_dd.copy(), figname='budyko_f')
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[5/7] Figure: Budyko Sigma (budyko_s) ...")
    try:
        wb_aridity_sigma(res_opt.copy(), res_dd.copy(), figname='budyko_s')
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[6/7] Figure: ET Partitioning (SI_ET_partitioning) ...")
    try:
        # et_part uses WUS_FIGS_PATH directly (hardcoded path inside function)
        et_part(res_opt.copy())
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print("\n[7/7] SI Figure: piF vs piR scatter (SI_piRpiF) ...")
    try:
        piF_piR_scatter(res_dd.copy(), res_opt.copy())
        print("  Done.")
    except Exception as e:
        print(f"  FAILED: {e}")

    print(f"\n=== All figures written to: {os.environ['WUS_FIGS_PATH']} ===")


if __name__ == "__main__":
    generate_figures()
