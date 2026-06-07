
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
import os
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
BASE_PATH = '/scratch2/et97/oldscratch/Ozflux_data_full/Sapflux_australia/dowloaded/'
OUTPUT_DIR = 'analysis_output_v2'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# File Paths (from notebook)
FILE_SOIL_RC = "Robson_Creek_soil_water_potential_data_P4aYrBV.csv"
FILE_LEAF_RC = "Robson_Creek_Predawn_and_Midday_leaf_water_potential_data.csv"
FILE_INV = "RC_and_CB_inventory_data.csv" # Combined inventory
FILE_SAP_RC = "Robson_Creek_Sap_flux_data.xlsx"
FILE_SAP_CB = "Cow_Bay_Sap_flux_data.xlsx"

# Flux Tower Data Paths (hardcoded in notebook)
FLUX_PATH_RC = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_cosmos_v3_validFe/robsoncreek/RobsonCreek_PTJPLSM_v2.csv"
FLUX_PATH_CB = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/cowbay/CowBay_PTJPLSM_v2.csv"
FLUX_PATH_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/Wombat_State_Forest/Wombat_State_Forest_PTJPLSM_v2.csv"

# --- HELPER FUNCTIONS ---

def calculate_metrics(observed, predicted):
    """Calculates r, r2, rmse, and bias."""
    df_temp = pd.DataFrame({'obs': observed, 'pred': predicted}).dropna()
    if len(df_temp) < 10:
        return {'r': np.nan, 'r2': np.nan, 'rmse': np.nan, 'bias': np.nan}
    
    r = df_temp['obs'].corr(df_temp['pred'])
    r2 = r2_score(df_temp['obs'], df_temp['pred']) 
    rmse = np.sqrt(mean_squared_error(df_temp['obs'], df_temp['pred']))
    bias = (df_temp['pred'] - df_temp['obs']).mean()
    
    return {'r': r, 'r2': r2, 'rmse': rmse, 'bias': bias}

def clean_sap_data(df, threshold=60):
    """Robustly cleans sap flux data: detects date, sets index, forces numeric, filters outliers."""
    # 1. Detect and Set Date Index
    # Check for common names including 'DT' which is used in this dataset
    date_col_list = [c for c in df.columns if str(c).lower() in ['dt', 'timestamp', 'date', 'time', 'datetime']]
    if not date_col_list:
        # Fallback partial match (careful not to match 'data')
        date_col_list = [c for c in df.columns if 'time' in str(c).lower() or 'date' in str(c).lower()]
    
    if date_col_list:
        # Use simple heuristic: usually the first datetime-like column
        target_col = date_col_list[0]
        try:
            df['timestamp'] = pd.to_datetime(df[target_col], dayfirst=True) # Try dayfirst for Aus data
            df.set_index('timestamp', inplace=True)
            # Remove original date columns to ensure only sensor data remains
            df = df.drop(columns=date_col_list) 
        except Exception as e:
            print(f"    Warning: Date parsing issue on {target_col}: {e}")
    
    # 2. Force Numeric (Coerce errors to NaN)
    # This ensures that any remaining string columns (like comments or units) become NaN
    df = df.apply(pd.to_numeric, errors='coerce')
    
    # 3. Filter by Threshold
    df[df > threshold] = np.nan
    df[df < 0] = np.nan
    
    return df

def process_rc_cb_site(site_code, sap_file, flux_file, inv_df, site_name, area_m2=2500, sapwood_proportion=0.6):
    """Process Robson Creek or Cow Bay sites with Basal Area Scaling."""
    print(f"\nProcessing {site_name} ({site_code})...")
    
    # 1. Load Inventory and Scale
    print("  -> Loading Inventory...")
    inv_site = inv_df[inv_df['Site'] == site_code]
    
    inv_site['BasalArea_cm2'] = np.pi * (inv_site['DBH'] / 2)**2
    total_basal_area_cm2 = inv_site['BasalArea_cm2'].sum()
    
    total_sapwood_area_cm2 = total_basal_area_cm2 * sapwood_proportion
    print(f"     Total Basal Area: {total_basal_area_cm2:.2f} cm2")
    
    # 2. Load Sap Flux Data
    full_sap_path = os.path.join(BASE_PATH, sap_file)
    print(f"  -> Loading Sap Flux: {sap_file}...")
    if sap_file.endswith('.xlsx'):
        df_sap = pd.read_excel(full_sap_path, engine='openpyxl')
    else:
        df_sap = pd.read_csv(full_sap_path)
    
    # Clean Data
    df_sap = clean_sap_data(df_sap, threshold=60)
    
    # Calculate Mean Velocity (cm/hr)
    velocity_median = df_sap.median(axis=1) # cm/hr
    
    # Upscale to Plot (mm/day)
    # Formula: F (mm/day) = (V * As) / Ap * 0.024
    sap_flux_plot_mm_day = (velocity_median * total_sapwood_area_cm2 / area_m2) * 0.024
    
    # Resample to daily (assuming input is average rate cm/hr, standard is mean * 24)
    sap_daily = sap_flux_plot_mm_day.resample('D').mean() * 24
    
    # 3. Load & Process Flux Tower Data
    print(f"  -> Loading Model Data: {flux_file}...")
    if not os.path.exists(flux_file):
        flux_file = flux_file.replace('/fs04', '')
        
    if os.path.exists(flux_file):
        df_flux = pd.read_csv(flux_file)
        if 'time' in df_flux.columns:
            df_flux['time'] = pd.to_datetime(df_flux['time'])
            df_flux.set_index('time', inplace=True)
        
        LHV = 2450000
        SECS = 86400
        
        df_models = pd.DataFrame(index=df_flux.index)
        
        if 'SM_LE_canopy' in df_flux.columns:
            df_models['SM'] = (df_flux['SM_LE_canopy'] * SECS) / LHV
        if 'Base_LE_canopy' in df_flux.columns:
            df_models['Base'] = (df_flux['Base_LE_canopy'] * SECS) / LHV
        if 'COSMOS_LE_canopy' in df_flux.columns: 
             df_models['COSMOS'] = (df_flux['COSMOS_LE_canopy'] * SECS) / LHV
        elif 'SM_LE_canopy' in df_flux.columns:
             df_models['COSMOS'] = df_models['SM']
             
        models_daily = df_models.resample('D').mean()
        
        merged = pd.concat([sap_daily.rename('SapFlux'), models_daily], axis=1).dropna()
        
        merged.to_csv(os.path.join(OUTPUT_DIR, f"{site_name}_processed.csv"))
        plot_site(site_name, merged)
        
        return merged
    else:
        print(f"  !! Flux file not found: {flux_file}")
        return None

def process_wombat_site(site_name="Wombat", sai=0.003):
    """Process Wombat State Forest with updated SAI."""
    print(f"\nProcessing {site_name}...")
    
    # 1. Load Sap Flux
    # 1. Load Sap Flux
    search_dir = os.path.join(BASE_PATH)
    
    # Robust search
    wombat_files = [f for f in os.listdir(search_dir) if "Wombat" in f and "P2G2F8K" in f and f.endswith(".csv")]
    
    if not wombat_files:
        print(f"  !! Wombat Sap Flux file not found in {search_dir}")
        print(f"     Subfiles: {[f for f in os.listdir(search_dir) if 'Wombat' in f]}")
        return None
        
    wombat_file = wombat_files[0]
    full_path = os.path.join(search_dir, wombat_file)
    print(f"  -> Found Sap File: {wombat_file}")
    
    df_sap = pd.read_csv(full_path)
    
    # Clean Data
    df_sap = clean_sap_data(df_sap, threshold=100)
    
    # Velocity (cm/hr)
    velocity_mean = df_sap.mean(axis=1)
    
    # Scaling
    print(f"     Using SAI: {sai}")
    sap_flux_daily = (velocity_mean.resample('D').mean() * 24 * 10 * sai)
    
    # 2. Load Model Data
    flux_file = FLUX_PATH_WOM
    if not os.path.exists(flux_file):
        flux_file = flux_file.replace('/fs04', '')
    
    if os.path.exists(flux_file):
        df_flux = pd.read_csv(flux_file)
        df_flux['time'] = pd.to_datetime(df_flux['time'])
        df_flux.set_index('time', inplace=True)
        
        LHV = 2450000
        SECS = 86400
        
        df_models = pd.DataFrame(index=df_flux.index)
        if 'SM_LE_canopy' in df_flux.columns:
            df_models['SM'] = (df_flux['SM_LE_canopy'] * SECS) / LHV
        if 'Base_LE_canopy' in df_flux.columns:
            df_models['Base'] = (df_flux['Base_LE_canopy'] * SECS) / LHV
            
        models_daily = df_models.resample('D').mean()
        
        merged = pd.concat([sap_flux_daily.rename('SapFlux'), models_daily], axis=1).dropna()
        
        merged.to_csv(os.path.join(OUTPUT_DIR, f"{site_name}_processed.csv"))
        plot_site(site_name, merged)
        
        return merged
    else:
        print(f"  !! Model file not found: {flux_file}")
        return None

def plot_site(site_name, df):
    """Generates and saves plot with metrics."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plotting
    ax.plot(df.index, df['SapFlux'], label='Sap Flux (Observed)', color='green', linewidth=2, alpha=0.8)
    
    if 'Base' in df.columns:
        ax.plot(df.index, df['Base'], label='PT-JPL (Base)', color='gray', linestyle='--', alpha=0.6)
    if 'SM' in df.columns:
        ax.plot(df.index, df['SM'], label='PT-JPL-SM (Soil Moisture)', color='blue', linestyle='-.', alpha=0.8)
    if 'COSMOS' in df.columns and 'SM' not in df.columns:
         ax.plot(df.index, df['COSMOS'], label='PT-JPL-SM (COSMOS)', color='blue', linestyle='-.', alpha=0.8)

    ax.set_title(f"{site_name}: Improved Scaling Validation", fontsize=14)
    ax.set_ylabel("Transpiration (mm/day)")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Calculate and Display Metrics
    stats_lines = []
    
    # Helper to format metrics
    def format_metrics(name, obs, pred):
        m = calculate_metrics(obs, pred)
        return (f"$\\bf{{{name}}}$\n"
                f"R: {m['r']:.2f}, R2: {m['r2']:.2f}\n"
                f"RMSE: {m['rmse']:.2f}, Bias: {m['bias']:.2f}")

    if 'SM' in df.columns:
        stats_lines.append(format_metrics('PT-JPL-SM', df['SapFlux'], df['SM']))
    elif 'COSMOS' in df.columns:
         stats_lines.append(format_metrics('PT-JPL-SM (COSMOS)', df['SapFlux'], df['COSMOS']))
         
    if 'Base' in df.columns:
        stats_lines.append(format_metrics('Base', df['SapFlux'], df['Base']))
        
    if stats_lines:
        stats_text = "\n\n".join(stats_lines)
        ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(facecolor='white', edgecolor='#dddddd', alpha=0.9, boxstyle='round,pad=0.5'))
    
    out_path = os.path.join(OUTPUT_DIR, f"{site_name.replace(' ', '_')}_comparison.png")
    plt.savefig(out_path, dpi=300)
    print(f"  -> Plot saved to {out_path}")
    plt.close()

# --- MAIN EXECUTION ---

# 1. Load Inventory
print("Loading Main Data...")
inv_df = pd.read_csv(os.path.join(BASE_PATH, FILE_INV))

# 2. Process Sites
results = []

# Robson Creek
df_rc = process_rc_cb_site("RC", FILE_SAP_RC, FLUX_PATH_RC, inv_df, "Robson Creek", area_m2=2500, sapwood_proportion=0.6)
if df_rc is not None:
    results.append(('Robson Creek', df_rc))

# Cow Bay
df_cb = process_rc_cb_site("CB", FILE_SAP_CB, FLUX_PATH_CB, inv_df, "Cow Bay", area_m2=2500, sapwood_proportion=0.6)
if df_cb is not None:
    results.append(('Cow Bay', df_cb))

# Wombat
df_wom = process_wombat_site("Wombat", sai=0.003)
if df_wom is not None:
    results.append(('Wombat', df_wom))

# 3. Print Statistics Table
print("\n" + "="*95)
print(f"{'SITE':<12} | {'MODEL':<8} | {'r (Corr)':<8} | {'R2':<8} | {'RMSE':<8} | {'BIAS':<8} | {'MEAN_OBS':<8}")
print("="*95)

for name, df in results:
    mean_obs = df['SapFlux'].mean()
    
    # Identify models
    models = []
    if 'Base' in df.columns: models.append('Base')
    if 'SM' in df.columns: models.append('SM')
    if 'COSMOS' in df.columns and 'SM' not in models: models.append('COSMOS')
    
    for model in models:
        m = calculate_metrics(df['SapFlux'], df[model])
        print(f"{name:<12} | {model:<8} | {m['r']:<8.3f} | {m['r2']:<8.3f} | {m['rmse']:<8.3f} | {m['bias']:<8.3f} | {mean_obs:<8.3f}")

print("-" * 95)
print(f"Results and Plots saved to: {OUTPUT_DIR}")
