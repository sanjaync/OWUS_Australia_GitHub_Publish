import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
import os
import seaborn as sns

# Config
DATA_DIR = "validation_data"
MODEL_RES_OPT = "output_corrected/combined/results_opt__ozflux_1.csv"
MODEL_RES_BF = "output_corrected/combined/results_bf__ozflux_1.csv"
OUT_DIR = "plots_corrected/validation_apd_sapflux"
os.makedirs(OUT_DIR, exist_ok=True)

SITES = {
    'AU-Rob': {
        'name': 'Robson Creek',
        'p50_file': 'Robson_Creek_pneumatic_vulnerability_curve_data.csv',
        'wp_file': 'Robson_Creek_Predawn_and_Midday_leaf_water_potential_data.csv'
    },
    'AU-Cow': {
        'name': 'Cow Bay',
        'p50_file': 'Cow_Bay__pneumatic_vulnerability_curve_data.csv',
        'wp_file': 'Cow_Bay_Predawn_and_Midday_leaf_water_potential_data.csv'
    }
}

import pickle

def load_model_results():
    """Load model results (Opt, BF) and Baseline results (Pickles)."""
    print("Loading Model & Baseline Results...")
    res_opt = pd.read_csv(MODEL_RES_OPT)
    res_bf = pd.read_csv(MODEL_RES_BF) if os.path.exists(MODEL_RES_BF) else None
    
    model_data = {}
    for site in SITES.keys():
        site_data = {'Site': site}
        
        # 1. Baseline (from input pickles)
        pickle_path = f"input_data/{site}_params.pickle"
        if os.path.exists(pickle_path):
            with open(pickle_path, 'rb') as f:
                p = pickle.load(f)
                site_data['Px50_BL'] = p.get('Px50', np.nan)
                site_data['Pg50_BL'] = p.get('Pg50', np.nan)
        
        # 2. Optimized (Opt) - Prefer Mean over MAP for validation
        row_opt = res_opt[res_opt['siteID'] == site]
        if not row_opt.empty:
            # Use MEAN for the primary comparison as it matches biology better
            site_data['Px50_Opt'] = row_opt.iloc[0].get('Px50_mean', row_opt.iloc[0]['Px50'])
            site_data['Pg50_Opt'] = row_opt.iloc[0].get('Pg50_mean', row_opt.iloc[0]['Pg50'])
            
            # Keep MAP for reference/whisker if needed
            site_data['Px50_MAP'] = row_opt.iloc[0]['Px50']
            site_data['Pg50_MAP'] = row_opt.iloc[0]['Pg50']
            site_data['NSE_Opt'] = row_opt.iloc[0]['NSE']
        
        # 3. Bayesian Fit (BF)
        if res_bf is not None:
            row_bf = res_bf[res_bf['siteID'] == site]
            if not row_bf.empty:
                site_data['Px50_BF'] = row_bf.iloc[0]['Px50']
                site_data['Pg50_BF'] = row_bf.iloc[0]['Pg50']
                site_data['NSE_BF'] = row_bf.iloc[0]['NSE']
                
        model_data[site] = site_data
        
    return model_data

def load_observations():
    """Load and process observation data."""
    print("Loading Observations...")
    obs_data = {}
    
    for site, info in SITES.items():
        print(f"  Processing {site} ({info['name']})...")
        site_obs = {}
        
        # 1. P50 (Vulnerability Curves)
        p50_path = os.path.join(DATA_DIR, info['p50_file'])
        if os.path.exists(p50_path):
            # Checking header structure: Line 1 is Units, Line 2 is Header
            # So we skip 1 row
            try:
                df_p50 = pd.read_csv(p50_path, skiprows=1)
            except Exception:
                # Fallback if standard read fails
                df_p50 = pd.read_csv(p50_path)

            # Check column name
            p50_col = 'P50' if 'P50' in df_p50.columns else None
            if p50_col:
                # Values are usually positive magnitude in these files (MPa)
                # We need negative for potential.
                vals = df_p50[p50_col].dropna()
                # If mean is positive, flip it. If negative, keep it.
                if vals.mean() > 0:
                    vals = -vals
                
                site_obs['P50_mean'] = vals.mean()
                site_obs['P50_std'] = vals.std()
                site_obs['P50_n'] = len(vals)
                site_obs['Species_P50'] = df_p50['SP'].unique().tolist() if 'SP' in df_p50 else []
            else:
                print(f"    Warning: P50 column not found in {info['p50_file']}")
        else:
            print(f"    Warning: File not found {p50_path}")

        # 2. Leaf Water Potential
        wp_path = os.path.join(DATA_DIR, info['wp_file'])
        if os.path.exists(wp_path):
            df_wp = pd.read_csv(wp_path)
            # Filter for Midday (MD)
            # Column usually "Predawn (PD) or Midday (MD)"
            # Check exact column name
            type_col = [c for c in df_wp.columns if 'Predawn' in c or 'MD' in c][0]
            val_col = [c for c in df_wp.columns if 'WP' in c or 'MPa' in c][0]
            
            md_vals = df_wp[df_wp[type_col] == 'MD'][val_col].dropna()
            pd_vals = df_wp[df_wp[type_col] == 'PD'][val_col].dropna()
            
            if not md_vals.empty:
                site_obs['Psi_MD_mean'] = md_vals.mean()
                site_obs['Psi_MD_min'] = md_vals.min()
                site_obs['Psi_MD_std'] = md_vals.std()
            
            if not pd_vals.empty:
                site_obs['Psi_PD_mean'] = pd_vals.mean()
                
        else:
             print(f"    Warning: File not found {wp_path}")
             
        obs_data[site] = site_obs
        
    return obs_data


def plot_comparison(model_data, obs_data):
    """Generate 3-way comparison plots."""
    print("Generating Tripartite Plots...")
    sites = list(SITES.keys())
    
    # Bar plot of P50
    p50_mod = [model_data[s].get('Px50_Opt', np.nan) for s in sites]
    p50_bl  = [model_data[s].get('Px50_BL', np.nan) for s in sites]
    p50_obs = [obs_data[s].get('P50_mean', np.nan) for s in sites]
    p50_obs_err = [obs_data[s].get('P50_std', 0) for s in sites]
    
    x = np.arange(len(sites))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.bar(x - width, p50_obs, width, yerr=p50_obs_err, label='Observed (Field)', capsize=5, color='forestgreen', alpha=0.8)
    ax.bar(x, p50_bl, width, label='Baseline (Literature)', color='gray', alpha=0.7)
    ax.bar(x + width, p50_mod, width, label='Optimized (EEO)', color='salmon')
    
    ax.set_ylabel('P50 / Px50 (MPa)')
    ax.set_title('Hydraulic Vulnerability (P50): Comparison of 3 Methods')
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\n({SITES[s]['name']})" for s in sites])
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    out_file = os.path.join(OUT_DIR, "P50_Tri_Validation_Bar.png")
    plt.savefig(out_file)
    print(f"Saved {out_file}")
    
    # Safety Margin Plot (3-way)
    fig, ax = plt.subplots(figsize=(10, 7))
    
    colors = {'Obs': 'forestgreen', 'BL': 'gray', 'Opt': 'salmon'}
    
    for i, s in enumerate(sites):
        # 1. Observed
        obs_p50 = obs_data[s].get('P50_mean', np.nan)
        obs_min = obs_data[s].get('Psi_MD_mean', np.nan)
        if not np.isnan(obs_p50) and not np.isnan(obs_min):
            ax.plot([i-0.2, i-0.2], [obs_min, obs_p50], color=colors['Obs'], ls='-', lw=2)
            ax.plot(i-0.2, obs_min, 'o', color=colors['Obs'], label='Observed' if i==0 else "")
            ax.plot(i-0.2, obs_p50, 'x', color=colors['Obs'], ms=8)

        # 2. Baseline
        bl_p50 = model_data[s].get('Px50_BL', np.nan)
        bl_min = model_data[s].get('Pg50_BL', np.nan)
        if not np.isnan(bl_p50) and not np.isnan(bl_min):
            ax.plot([i, i], [bl_min, bl_p50], color=colors['BL'], ls='-', lw=2)
            ax.plot(i, bl_min, 'o', color=colors['BL'], label='Baseline' if i==0 else "")
            ax.plot(i, bl_p50, 'x', color=colors['BL'], ms=8)
            
        # 3. Optimized
        opt_p50 = model_data[s].get('Px50_Opt', np.nan)
        opt_min = model_data[s].get('Pg50_Opt', np.nan)
        if not np.isnan(opt_p50) and not np.isnan(opt_min):
            ax.plot([i+0.2, i+0.2], [opt_min, opt_p50], color=colors['Opt'], ls='-', lw=2)
            ax.plot(i+0.2, opt_min, 'o', color=colors['Opt'], label='Optimized' if i==0 else "")
            ax.plot(i+0.2, opt_p50, 'x', color=colors['Opt'], ms=8)
            
    ax.set_xticks(range(len(sites)))
    ax.set_xticklabels([f"{s}" for s in sites])
    ax.set_ylabel("Water Potential (MPa)")
    ax.set_title("Hydraulic Safety Margins: Baseline vs Optimized vs Observed")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.invert_yaxis() # Potentials are negative, bigger magnitude at bottom
    
    plt.tight_layout()
    out_file = os.path.join(OUT_DIR, "HSM_Tri_Validation.png")
    plt.savefig(out_file)
    print(f"Saved {out_file}")

def print_report(model_data, obs_data):
    """Print tripartite report."""
    print("\n" + "="*60)
    print("TRIPARTITE VALIDATION: BASELINE vs OPTIMIZED vs OBSERVED")
    print("="*60)
    
    for s in SITES.keys():
        print(f"\nSITE: {s} ({SITES[s]['name']})")
        
        # Obs
        o = obs_data[s]
        p50_o = o.get('P50_mean', np.nan)
        psi_md = o.get('Psi_MD_mean', np.nan)
        hsm_o = psi_md - p50_o
        
        # BL
        bl = model_data[s]
        p50_bl = bl.get('Px50_BL', np.nan)
        pg50_bl = bl.get('Pg50_BL', np.nan)
        hsm_bl = pg50_bl - p50_bl
        
        # Opt
        m = model_data[s]
        p50_m = m.get('Px50_Opt', np.nan)
        pg50_m = m.get('Pg50_Opt', np.nan)
        hsm_m = pg50_m - p50_m
        
        print(f"  {'METHOD':<12} | {'P50 (Px50)':<10} | {'Psi_min(Pg50)':<12} | {'HSM':<6}")
        print(f"  {'-'*12}-+-{'-'*10}-+-{'-'*12}-+-{'-'*6}")
        print(f"  {'OBSERVED':<12} | {p50_o:>10.2f} | {psi_md:>12.2f} | {hsm_o:>6.2f}")
        print(f"  {'BASELINE':<12} | {p50_bl:>10.2f} | {pg50_bl:>12.2f} | {hsm_bl:>6.2f}")
        print(f"  {'OPTIMIZED':<12} | {p50_m:>10.2f} | {pg50_m:>12.2f} | {hsm_m:>6.2f}")
        
        print(f"\n  BIAS (vs Observed):")
        print(f"    Baseline Bias:  {p50_bl - p50_o:>6.2f} MPa")
        print(f"    Optimized Bias: {p50_m - p50_o:>6.2f} MPa")

if __name__ == "__main__":
    m_data = load_model_results()
    o_data = load_observations()
    print_report(m_data, o_data)
    plot_comparison(m_data, o_data)
