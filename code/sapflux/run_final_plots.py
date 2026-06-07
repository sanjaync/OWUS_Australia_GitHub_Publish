
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from sklearn.metrics import mean_squared_error, r2_score
import warnings

warnings.filterwarnings('ignore')

# =================================================
# 1. GLOBAL CONFIGURATION & STYLE
# =================================================
# Paths
BASE_SAP_RC_CB = '/scratch2/et97/oldscratch/Ozflux_data_full/Sapflux_australia/dowloaded/'
BASE_FLUX_RC_CB = '/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/'
BASE_FLUX_RC_COSMOS = '/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_cosmos_v3_validFe/'

# Check for Wombat path
BASE_SAP_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/sapfluxnet/extracted_data/0.1.5/csv/sapwood/"
BASE_FLUX_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/wombatstateforest1/"

OUTPUT_DIR = 'analysis_output_final'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Constants
LHV = 2450000          # Latent Heat of Vaporization (J/kg)
SECONDS_IN_DAY = 86400
W_M2_TO_MM_DAY = 1 / 28.35  # Approx conversion factor for Wombat

# Plotting Style (Nature/Science)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 1.2

# =================================================
# 2. HELPER: METRICS
# =================================================
def calculate_metrics(observed, predicted):
    """
    Calculates R (Pearson), R2 (Score), RMSE, and Bias.
    """
    # Align data by dropping NaNs in either series
    df_temp = pd.DataFrame({'obs': observed, 'pred': predicted}).dropna()
    
    if len(df_temp) < 10:
        return {'r': np.nan, 'r2': np.nan, 'rmse': np.nan, 'bias': np.nan}
        
    obs = df_temp['obs']
    pred = df_temp['pred']

    r = obs.corr(pred)
    r2 = r2_score(obs, pred)
    rmse = np.sqrt(mean_squared_error(obs, pred))
    bias = np.mean(pred - obs) # Positive = Overestimation, Negative = Underestimation
    
    return {'r': r, 'r2': r2, 'rmse': rmse, 'bias': bias}

# =================================================
# 3. PROCESSING FUNCTIONS
# =================================================

def process_rc_cb_site(sap_file, inventory_code, flux_subpath, area_m2):
    """Process Robson Creek or Cow Bay using the Excel/Inventory scaling method."""
    print(f"Processing {inventory_code}...")
    
    # A. Load Sap Flux & Inventory
    sap_path = os.path.join(BASE_SAP_RC_CB, sap_file)
    inv_path = os.path.join(BASE_SAP_RC_CB, 'RC_and_CB_inventory_data.csv')
    
    if not os.path.exists(sap_path):
        print(f"  !! Sap file missing: {sap_path}")
        return pd.DataFrame()

    df_sap = pd.read_excel(sap_path, engine='openpyxl')
    df_inv = pd.read_csv(inv_path)

    # Time Index
    # Check for common names including 'DT'
    time_cols = [c for c in df_sap.columns if str(c).lower() in ['dt', 'timestamp', 'date', 'time', 'datetime']]
    if not time_cols:
        time_cols = [c for c in df_sap.columns if 'date' in str(c).lower() or 'time' in str(c).lower()]
    
    if not time_cols:
        print(f"  !! No time column found in {sap_file}. Cols: {df_sap.columns}")
        return pd.DataFrame()
        
    time_col = time_cols[0]
    df_sap[time_col] = pd.to_datetime(df_sap[time_col])
    df_sap.set_index(time_col, inplace=True)
    
    # Cleaning
    df_sap = df_sap.select_dtypes(include=[np.number])
    df_sap[df_sap > 100] = np.nan
    df_sap[df_sap < 0] = np.nan

    # Scale Sap Flux
    inv_site = df_inv[df_inv['Site'] == inventory_code]
    c_plot_total = (inv_site['DBH'] * np.pi).sum()
    
    # Scaling: Median Rate (kg/cm/hr) * Total Circ (cm) * 1 / Area (m2)
    # Using Median as per user code
    t_plot_mm_hr = (df_sap.median(axis=1) * c_plot_total) / area_m2
    t_daily_sap = t_plot_mm_hr.resample('D').sum()

    # B. Load Flux Tower
    flux_path = os.path.join(BASE_FLUX_RC_CB, flux_subpath)
    if not os.path.exists(flux_path): flux_path = flux_path.replace('/fs04', '')
    
    if os.path.exists(flux_path):
        df_flux = pd.read_csv(flux_path)
        if 'time' in df_flux.columns:
            df_flux['time'] = pd.to_datetime(df_flux['time'])
            df_flux.set_index('time', inplace=True)
            
        print(f"DEBUG: Flux columns for {inventory_code}: {df_flux.columns.tolist()}")
        if 'COSMOS_LE_canopy' in df_flux.columns:
            print("DEBUG: COSMOS column found!")

        # Clean columns
        df_flux.columns = [c.strip() for c in df_flux.columns]
        
        # Convert Units (W/m2 -> mm/day)
        flux_obs = (df_flux['LE_Obs'] * SECONDS_IN_DAY) / LHV
        flux_base = (df_flux['Base_LE_canopy'] * SECONDS_IN_DAY) / LHV
        flux_sm = (df_flux['SM_LE_canopy'] * SECONDS_IN_DAY) / LHV
        
        # Core dataframe
        df_res = pd.DataFrame({
            'SapFlux': t_daily_sap,
            'ET_Obs': flux_obs.resample('D').mean(),
            'Base': flux_base.resample('D').mean(),
            'SM': flux_sm.resample('D').mean()
        })
        
        if 'COSMOS_LE_canopy' in df_flux.columns:
            print("  -> Adding COSMOS data...")
            flux_cosmos = (df_flux['COSMOS_LE_canopy'] * SECONDS_IN_DAY) / LHV
            df_res['COSMOS'] = flux_cosmos.resample('D').mean()
            
        # Drop rows where SapFlux or Base/SM are missing (Validation Requirement)
        # But if COSMOS is missing, we might still want to keep the row for main plot?
        # For this specific request, let's keep intersection of Data and Models.
        return df_res.dropna()
    else:
        print(f"  !! Flux file missing: {flux_path}")
        return pd.DataFrame()

def process_wombat_site():
    """Process Wombat State Forest using the SapFluxNet CSV method."""
    print("Processing Wombat...")
    
    # A. Load Sap Flux
    sapf_path = os.path.join(BASE_SAP_WOM, "AUS_WOM_sapf_data.csv")
    plant_path = os.path.join(BASE_SAP_WOM, "AUS_WOM_plant_md.csv")
    
    # Fallback search if exact path fails (Environment issues)
    if not os.path.exists(sapf_path):
        print(f"  !! Wombat SapFluxNet file not found at {sapf_path}")
        # Try local download folder as fallback if user moved it
        local_sap = os.path.join(BASE_SAP_RC_CB, "AUS_WOM_sapf_data.csv")
        if os.path.exists(local_sap):
            sapf_path = local_sap
            plant_path = os.path.join(BASE_SAP_RC_CB, "AUS_WOM_plant_md.csv")
        else:
            return pd.DataFrame()

    sap = pd.read_csv(sapf_path)
    plants = pd.read_csv(plant_path)

    sap["TIMESTAMP"] = pd.to_datetime(sap["TIMESTAMP"], utc=True)
    sap = sap.set_index("TIMESTAMP").sort_index()
    try:
        sap = sap.loc["2013-01-01":"2015-10-31"]
    except: pass # Use available range

    # Cleaning & Scaling
    sap_cols = [c for c in sap.columns if "Js" in c]
    sap[sap_cols] = sap[sap_cols].where((sap[sap_cols] >= 0) & (sap[sap_cols] <= 60))
    
    # Use plant metadata for robust scaling
    try:
        sapwood_area = plants.set_index("pl_code")["pl_sapw_area"][sap_cols]
        total_sapwood_cm2 = sapwood_area.sum()
        
        # Calculate Volume -> Velocity -> Transpiration
        tree_vol = sap[sap_cols] * sapwood_area * 0.5 # dt_hours (assuming 30min data? SapFluxNet usually is)
        # Actually SapFluxNet Js units are usually cm/h or g m-2 s-1. 
        # User code assumes simple multiplication. Let's stick to user logic:
        # User: tree_vol = sap * sapwood_area * 0.5
        
        daily_vol = tree_vol.resample("D").sum().sum(axis=1) # Total volume per day for stand
        stand_velocity = (daily_vol / total_sapwood_cm2) * 10 # ??? User logic.
        
        SAI = 0.001 # User's fixed SAI
        t_daily_sap = stand_velocity * SAI
        
        # Remove TZ for merging
        t_daily_sap.index = t_daily_sap.index.tz_localize(None)
    except Exception as e:
        print(f"  Error processing Wombat Sap: {e}")
        return pd.DataFrame()

    # B. Load Flux Tower
    flux_path = os.path.join(BASE_FLUX_WOM, "WombatStateForest1_PTJPLSM_v2.csv")
    if not os.path.exists(flux_path): 
        # Try generic name
        flux_path = os.path.join(BASE_FLUX_WOM, "Wombat_State_Forest_PTJPLSM_v2.csv")
        if not os.path.exists(flux_path):
            flux_path = flux_path.replace('/fs04', '')
    
    if not os.path.exists(flux_path):
        print(f"  !! Wombat Flux file not found: {flux_path}")
        return pd.DataFrame()
        
    ft = pd.read_csv(flux_path)
    ft["time"] = pd.to_datetime(ft["time"])
    ft = ft.set_index("time").sort_index()
    try:
        ft = ft.loc["2013-01-01":"2015-10-31"]
    except: pass
    
    # Units (Using the fixed constant)
    if "LE_Obs" in ft.columns:
        flux_obs = ft["LE_Obs"] * W_M2_TO_MM_DAY
        flux_sm = ft["SM_LE_canopy"] * W_M2_TO_MM_DAY
        flux_base = ft["Base_LE_canopy"] * W_M2_TO_MM_DAY

        return pd.DataFrame({
            'SapFlux': t_daily_sap,
            'ET_Obs': flux_obs,
            'Base': flux_base,
            'SM': flux_sm
        }).dropna()
    return pd.DataFrame()

# =================================================
# 4. PLOTTING FUNCTION
# =================================================
def plot_site(ax, df, site_name, show_legend=False):
    if df.empty:
        ax.text(0.5, 0.5, "No Data", ha='center')
        return

    # Colors
    col_obs = '#999999'       # Light Grey
    col_base = '#d95f02'      # Vermilion
    col_sm = '#1b9e77'        # Teal
    col_sap = '#00468b'       # Blue

    # 1. Flux Tower Total ET (Background)
    if 'ET_Obs' in df.columns:
        ax.fill_between(df.index, df['ET_Obs'], color=col_obs, alpha=0.3, label='Observed Total ET')
    
    # 2. Models
    ax.plot(df.index, df['Base'], color=col_base, linestyle='--', linewidth=1.2, alpha=0.8, label='PT-JPL Base')
    ax.plot(df.index, df['SM'], color=col_sm, linestyle='-', linewidth=1.5, alpha=0.9, label='PT-JPL-SM')

    # 3. Sap Flux (Foreground)
    ax.plot(df.index, df['SapFlux'], color=col_sap, linewidth=1.8, alpha=1.0, label='Sap Flow')

    # Styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', width=1.2, length=5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    
    ax.set_title(site_name, loc='left', fontweight='bold', fontsize=12)
    ax.set_ylabel("Transpiration\n($mm \cdot d^{-1}$)", fontsize=10)
    ax.grid(axis='y', linestyle=':', alpha=0.3)

    # Stats
    m_sm = calculate_metrics(df['SapFlux'], df['SM'])
    m_base = calculate_metrics(df['SapFlux'], df['Base'])
    
    # Formatted Stats Block with R included
    stats_text = (
        f"$\\bf{{PT-JPL-SM}}$\n"
        f"R: {m_sm['r']:.2f}, R2: {m_sm['r2']:.2f}\n"
        f"RMSE: {m_sm['rmse']:.2f}, Bias: {m_sm['bias']:.2f}\n\n"
        f"$\\bf{{Base}}$\n"
        f"R: {m_base['r']:.2f}, R2: {m_base['r2']:.2f}\n"
        f"RMSE: {m_base['rmse']:.2f}, Bias: {m_base['bias']:.2f}"
    )
    
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', bbox=dict(facecolor='white', edgecolor='#dddddd', alpha=0.9, boxstyle='round,pad=0.5'))

    if show_legend:
        ax.legend(frameon=False, loc='upper right', fontsize=9, ncol=4)

# =================================================
# 5. MAIN EXECUTION
# =================================================

# Prepare Data
# 1. Standard RC Data (Base + Probe SM)
df_rc = process_rc_cb_site("Robson_Creek_Sap_flux_data.xlsx", "RC", "robsoncreek/RobsonCreek_PTJPLSM_v2.csv", 250000)

# 2. Merge COSMOS Data for RC
cosmos_path = os.path.join(BASE_FLUX_RC_COSMOS, "robsoncreek/RobsonCreek_PTJPLSM_v2.csv")
if os.path.exists(cosmos_path) and not df_rc.empty:
    print("  -> Merging separate COSMOS file for RC...")
    df_cos = pd.read_csv(cosmos_path)
    # Clean cols
    df_cos.columns = [c.strip() for c in df_cos.columns]
    
    if 'time' in df_cos.columns:
        df_cos['time'] = pd.to_datetime(df_cos['time'])
        df_cos.set_index('time', inplace=True)
        
        # The COSMOS model is the 'SM_LE_canopy' column in this specific file
        if 'SM_LE_canopy' in df_cos.columns:
            flux_cos = (df_cos['SM_LE_canopy'] * SECONDS_IN_DAY) / LHV
            flux_cos_daily = flux_cos.resample('D').mean()
            
            # Merge into df_rc
            # Use join to keep main index
            df_rc = df_rc.join(flux_cos_daily.rename('COSMOS'), how='inner') # Inner join to valid intersection? Or left?
            # User wants validation, so intersection is safest.
            
df_cb = process_rc_cb_site("Cow_Bay_Sap_flux_data.xlsx", "CB", "cowbay/CowBay_PTJPLSM_v2.csv", 8000)
df_wom = process_wombat_site()

# Plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharey=False)

fig.suptitle("Sapflux Site Validation", fontsize=16, fontweight='bold', y=0.98)

# Plot each site
plot_site(ax1, df_rc, "Robson Creek (Tropical Rainforest)", show_legend=True)
plot_site(ax2, df_cb, "Cow Bay (Tropical Rainforest)", show_legend=False)
plot_site(ax3, df_wom, "Wombat State Forest (Dry Sclerophyll)", show_legend=False)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(hspace=0.3)

out_file = os.path.join(OUTPUT_DIR, "final_comparison_plots.png")
plt.savefig(out_file, dpi=300)
print(f"Combined Plot saved to {out_file}")

# =================================================
# 6. PLOT RC WITH COSMOS
# =================================================
if 'COSMOS' in df_rc.columns:
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Colors
    col_obs = '#999999'
    col_base = '#d95f02'
    col_sm = '#1b9e77'
    col_cosmos = '#7570b3' # Purple
    col_sap = '#00468b'

    ax.fill_between(df_rc.index, df_rc['ET_Obs'], color=col_obs, alpha=0.3, label='Observed Total ET')
    ax.plot(df_rc.index, df_rc['Base'], color=col_base, ls='--', lw=1.2, alpha=0.8, label='Base')
    ax.plot(df_rc.index, df_rc['SM'], color=col_sm, ls='-', lw=1.5, alpha=0.9, label='SM')
    ax.plot(df_rc.index, df_rc['COSMOS'], color=col_cosmos, ls='-.', lw=1.5, alpha=0.9, label='COSMOS')
    ax.plot(df_rc.index, df_rc['SapFlux'], color=col_sap, lw=1.8, alpha=1.0, label='Sap Flow')
    
    ax.set_title("Robson Creek Validation (with COSMOS)", fontweight='bold')
    ax.set_ylabel("Transpiration (mm/day)")
    ax.legend(frameon=False, ncol=5, loc='upper right', fontsize=9)
    
    # Stats
    m_base = calculate_metrics(df_rc['SapFlux'], df_rc['Base'])
    m_sm = calculate_metrics(df_rc['SapFlux'], df_rc['SM'])
    m_cos = calculate_metrics(df_rc['SapFlux'], df_rc['COSMOS'])
    
    stats = (
        f"$\\bf{{COSMOS}}$\n"
        f"R: {m_cos['r']:.2f}, R2: {m_cos['r2']:.2f}\n"
        f"RMSE: {m_cos['rmse']:.2f}, Bias: {m_cos['bias']:.2f}\n\n"
        f"$\\bf{{SM}}$\n"
        f"R: {m_sm['r']:.2f}, R2: {m_sm['r2']:.2f}\n"
        f"RMSE: {m_sm['rmse']:.2f}, Bias: {m_sm['bias']:.2f}\n\n"
        f"$\\bf{{Base}}$\n"
        f"R: {m_base['r']:.2f}, R2: {m_base['r2']:.2f}\n"
        f"RMSE: {m_base['rmse']:.2f}, Bias: {m_base['bias']:.2f}"
    )
    ax.text(0.02, 0.95, stats, transform=ax.transAxes, fontsize=8, va='top', bbox=dict(facecolor='white', alpha=0.9, boxstyle='round,pad=0.5'))
    
    out_file = os.path.join(OUTPUT_DIR, "Robson_Creek_COSMOS_Validation.png")
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    print(f"RC COSMOS Plot saved to {out_file}")

# =================================================
# 7. PRINT DETAILED STATISTICS
# =================================================
print("\n" + "="*80)
print(f"{'SITE':<12} | {'MODEL':<8} | {'R':<6} | {'R2':<6} | {'RMSE':<6} | {'BIAS':<6} | {'MEAN_OBS':<8}")
print("="*80)

sites = [('Robson Creek', df_rc), ('Cow Bay', df_cb), ('Wombat', df_wom)]

for name, df in sites:
    if df.empty: continue
    mean_obs = df['SapFlux'].mean()
    
    models = ['Base', 'SM']
    if 'COSMOS' in df.columns: models.append('COSMOS')
    
    for mod in models:
        m = calculate_metrics(df['SapFlux'], df[mod])
        prefix = name if mod == models[0] else ""
        print(f"{prefix:<12} | {mod:<8} | {m['r']:<6.3f} | {m['r2']:<6.3f} | {m['rmse']:<6.3f} | {m['bias']:<6.3f} | {mean_obs:<8.3f}")
    print("-" * 80)
