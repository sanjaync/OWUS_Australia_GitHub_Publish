
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score
import os
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
BASE_PATH = '/scratch2/et97/oldscratch/Ozflux_data_full/Sapflux_australia/dowloaded/'
OUTPUT_DIR = 'analysis_output_calibration'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Files
FILE_INV = "RC_and_CB_inventory_data.csv"
FILE_SAP_RC = "Robson_Creek_Sap_flux_data.xlsx"
FILE_SAP_CB = "Cow_Bay_Sap_flux_data.xlsx"
FLUX_PATH_RC = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_cosmos_v3_validFe/robsoncreek/RobsonCreek_PTJPLSM_v2.csv"
FLUX_PATH_CB = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/cowbay/CowBay_PTJPLSM_v2.csv"
FLUX_PATH_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/Wombat_State_Forest/Wombat_State_Forest_PTJPLSM_v2.csv"

# --- HELPERS ---

def calculate_metrics(observed, predicted):
    df_temp = pd.DataFrame({'obs': observed, 'pred': predicted}).dropna()
    if len(df_temp) < 10:
        return {'r': np.nan, 'r2': np.nan, 'rmse': np.nan, 'bias': np.nan}
    
    r = df_temp['obs'].corr(df_temp['pred'])
    r2 = r2_score(df_temp['obs'], df_temp['pred'])
    rmse = np.sqrt(mean_squared_error(df_temp['obs'], df_temp['pred']))
    bias = (df_temp['pred'] - df_temp['obs']).mean()
    return {'r': r, 'r2': r2, 'rmse': rmse, 'bias': bias}

def clean_sap(df):
    # Detect date
    date_cols = [c for c in df.columns if str(c).lower() in ['dt', 'timestamp', 'date', 'time']]
    if not date_cols:
        date_cols = [c for c in df.columns if 'time' in str(c).lower() or 'date' in str(c).lower()]
        
    if date_cols:
        try:
            df['timestamp'] = pd.to_datetime(df[date_cols[0]], dayfirst=True)
            df.set_index('timestamp', inplace=True)
            df = df.drop(columns=date_cols)
        except: pass
        
    df = df.apply(pd.to_numeric, errors='coerce')
    df[df > 100] = np.nan
    df[df < 0] = np.nan
    return df

def calibrate_and_process(site_code, site_name, sap_file, flux_file, inv_df, plot_area=2500):
    print(f"\n--- Calibrating {site_name} ---")
    
    # 1. Inventory Factors
    inv_site = inv_df[inv_df['Site'] == site_code]
    
    # Factor A: Circumference Sum (Old Method)
    circ_sum = (inv_site['DBH'] * np.pi).sum()
    
    # Factor B: Basal Area Sum (Physical Method)
    ba_sum = (np.pi * (inv_site['DBH']/2)**2).sum()
    
    print(f"  Circumference Sum: {circ_sum:.1f}")
    print(f"  Basal Area Sum: {ba_sum:.1f}")
    
    # 2. Sap Velocity
    full_path = os.path.join(BASE_PATH, sap_file)
    if not os.path.exists(full_path):
        print(f"  !! File not found: {sap_file}")
        return None
        
    if sap_file.endswith('.xlsx'):
        df_sap = pd.read_excel(full_path, engine='openpyxl')
    else:
        df_sap = pd.read_csv(full_path)
        
    df_sap = clean_sap(df_sap)
    velocity = df_sap.median(axis=1) # cm/hr
    
    # 3. Model Data (Target)
    if not os.path.exists(flux_file): flux_file = flux_file.replace('/fs04', '')
    if not os.path.exists(flux_file):
        print("  !! Flux file missing")
        return None
        
    df_flux = pd.read_csv(flux_file)
    if 'time' in df_flux.columns:
        df_flux['time'] = pd.to_datetime(df_flux['time'])
        df_flux.set_index('time', inplace=True)
        
    # Get Target Model (Base)
    LHV = 2450000; SECS = 86400
    target_model = (df_flux['Base_LE_canopy'] * SECS / LHV).resample('D').mean()
    
    # 4. Construct Unscaled Sap Flux
    # We want: Flux_scaled = k * Velocity_daily
    # Where k includes (Area_Factor / Plot_Area * Units)
    
    # Raw Daily Velocity Sum (cm/day approx)
    # Using resample('D').mean() * 24 as standard.
    vel_daily = velocity.resample('D').mean() * 24
    
    # Align Data
    aligned = pd.concat([vel_daily, target_model], axis=1).dropna()
    aligned.columns = ['V', 'Target']
    
    # 5. Determine Optimal k
    # We want Mean(k * V) = Mean(Target)
    # k * Mean(V) = Mean(Target)
    # k = Mean(Target) / Mean(V)
    
    if aligned['V'].mean() == 0:
        print("  !! Zero velocity mean.")
        return None
        
    k_optimal = aligned['Target'].mean() / aligned['V'].mean()
    print(f"  Target Mean Flux: {aligned['Target'].mean():.4f} mm/day")
    print(f"  Velocity Mean:    {aligned['V'].mean():.4f} cm/day")
    print(f"  -> Optimal Scaling Factor (k): {k_optimal:.6f}")
    
    # Apply Calibration
    sap_final = vel_daily * k_optimal
    
    # 6. Save & Plot
    merged = pd.concat([sap_final.rename('SapFlux_Calibrated'), target_model.rename('Base')], axis=1).dropna()
    
    # Add Soil Moisture Model if exists
    if 'SM_LE_canopy' in df_flux.columns:
        sm_model = (df_flux['SM_LE_canopy'] * SECS / LHV).resample('D').mean()
        merged = pd.concat([merged, sm_model.rename('SM')], axis=1).dropna()
        
    merged.to_csv(os.path.join(OUTPUT_DIR, f"{site_name}_calibrated.csv"))
    
    # Calculate Metrics for Plot Legend
    m_base = calculate_metrics(merged['SapFlux_Calibrated'], merged['Base'])
    
    # Plot
    plt.figure(figsize=(12,6))
    plt.plot(merged.index, merged['SapFlux_Calibrated'], label='Sap Flux (Calibrated)', color='green', lw=2)
    plt.plot(merged.index, merged['Base'], label=f"Base (R={m_base['r']:.2f}, R2={m_base['r2']:.2f}, RMSE={m_base['rmse']:.2f}, Bias={m_base['bias']:.2f})", color='gray', ls='--', alpha=0.7)
    
    if 'SM' in merged.columns:
        m_sm = calculate_metrics(merged['SapFlux_Calibrated'], merged['SM'])
        plt.plot(merged.index, merged['SM'], label=f"SM (R={m_sm['r']:.2f}, R2={m_sm['r2']:.2f}, RMSE={m_sm['rmse']:.2f}, Bias={m_sm['bias']:.2f})", color='blue', ls='-.', alpha=0.7)
        
    plt.title(f"{site_name}: Calibrated Scaling")
    plt.ylabel("mm/day")
    plt.legend()
    plt.savefig(os.path.join(OUTPUT_DIR, f"{site_name}_calibrated.png"))
    plt.close()
    
    return merged, k_optimal

def process_wombat(site_name="Wombat"):
    print(f"\n--- Calibrating {site_name} ---")
    
    # Load Sap
    search_dir = BASE_PATH
    files = [f for f in os.listdir(search_dir) if "Wombat" in f and "P2G2F8K" in f and f.endswith(".csv")]
    if not files:
        print("  !! Wombat file not found")
        return None
    
    df_sap = pd.read_csv(os.path.join(search_dir, files[0]))
    # Date
    date_col = [c for c in df_sap.columns if 'time' in c.lower()][0]
    df_sap['timestamp'] = pd.to_datetime(df_sap[date_col], dayfirst=True)
    df_sap.set_index('timestamp', inplace=True)
    df_sap = df_sap.select_dtypes(include=[np.number])
    
    vel = df_sap.mean(axis=1)
    vel_daily = vel.resample('D').mean() * 24 # cm/day
    
    # Load Target
    flux_file = FLUX_PATH_WOM
    if not os.path.exists(flux_file): flux_file = flux_file.replace('/fs04', '')
    
    if os.path.exists(flux_file):
        df_flux = pd.read_csv(flux_file)
        df_flux['time'] = pd.to_datetime(df_flux['time'])
        df_flux.set_index('time', inplace=True)
        LHV = 2450000; SECS = 86400
        target = (df_flux['Base_LE_canopy'] * SECS / LHV).resample('D').mean()
        
        # Calibrate
        aligned = pd.concat([vel_daily, target], axis=1).dropna()
        k_optimal = aligned['Base_LE_canopy'].mean() / aligned[0].mean()
        print(f"  -> Optimal k: {k_optimal:.6f}")
        
        final = vel_daily * k_optimal
        merged = pd.concat([final.rename('SapFlux_Calibrated'), target.rename('Base')], axis=1).dropna()
        
        # Add SM
        if 'SM_LE_canopy' in df_flux.columns:
             sm = (df_flux['SM_LE_canopy'] * SECS / LHV).resample('D').mean()
             merged['SM'] = sm
             
        merged.to_csv(os.path.join(OUTPUT_DIR, f"{site_name}_calibrated.csv"))
        
        # Calculate Metrics
        m_base = calculate_metrics(merged['SapFlux_Calibrated'], merged['Base'])
        
        plt.figure(figsize=(12,6))
        plt.plot(merged.index, merged['SapFlux_Calibrated'], label='Sap Flux (Calibrated)', color='green')
        plt.plot(merged.index, merged['Base'], label=f"Base (R={m_base['r']:.2f}, R2={m_base['r2']:.2f}, RMSE={m_base['rmse']:.2f}, Bias={m_base['bias']:.2f})", color='gray', ls='--')
        
        if 'SM' in merged.columns:
             m_sm = calculate_metrics(merged['SapFlux_Calibrated'], merged['SM'])
             plt.plot(merged.index, merged['SM'], label=f"SM (R={m_sm['r']:.2f}, R2={m_sm['r2']:.2f}, RMSE={m_sm['rmse']:.2f}, Bias={m_sm['bias']:.2f})", color='blue', ls='-.')
             
        plt.legend()
        plt.title(f"{site_name}: Calibrated Scaling")
        plt.savefig(os.path.join(OUTPUT_DIR, f"{site_name}_calibrated.png"))
        plt.close()
        return merged, k_optimal
    return None, None

# --- MAIN ---
print("Loading Inventory...")
inv_df = pd.read_csv(os.path.join(BASE_PATH, FILE_INV))

res_rc, k_rc = calibrate_and_process("RC", "Robson Creek", FILE_SAP_RC, FLUX_PATH_RC, inv_df)
res_cb, k_cb = calibrate_and_process("CB", "Cow Bay", FILE_SAP_CB, FLUX_PATH_CB, inv_df)
res_wom, k_wom = process_wombat()

print("\n" + "="*95)
print(f"{'SITE':<12} | {'MODEL':<8} | {'r':<8} | {'RMSE':<8} | {'BIAS':<8} | {'MEAN_OBS':<8} | {'MEAN_MOD':<8}")
print("="*95)

for name, df in [('Robson Creek', res_rc), ('Cow Bay', res_cb), ('Wombat', res_wom)]:
    if df is not None:
        mean_obs = df['SapFlux_Calibrated'].mean()
        for mod in ['Base', 'SM']:
            if mod in df.columns:
                m = calculate_metrics(df['SapFlux_Calibrated'], df[mod])
                mean_mod = df[mod].mean()
                print(f"{name:<12} | {mod:<8} | {m['r']:<8.3f} | {m['rmse']:<8.3f} | {m['bias']:<8.3f} | {mean_obs:<8.3f} | {mean_mod:<8.3f}")
print("-" * 95)
