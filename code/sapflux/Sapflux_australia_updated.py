
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os
from sklearn.metrics import mean_squared_error, r2_score

# =================================================
# 1. GLOBAL CONFIGURATION & STYLE
# =================================================
# Paths
BASE_SAP_RC_CB = '/scratch2/et97/oldscratch/Ozflux_data_full/Sapflux_australia/dowloaded/'
BASE_FLUX_RC_CB = '/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/'

BASE_SAP_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/sapfluxnet/extracted_data/0.1.5/csv/sapwood/"
BASE_FLUX_WOM = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/ptjpl_ptjplsm/output_L6_validFe_v2/wombatstateforest1/"

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
    # Align data by dropping NaNs in either series
    df_temp = pd.DataFrame({'obs': observed, 'pred': predicted}).dropna()
    
    if len(df_temp) < 10:
        return np.nan, np.nan, np.nan, np.nan
        
    # 1. Correlation (r)
    r = df_temp['obs'].corr(df_temp['pred'])
    
    # 2. RMSE
    rmse = np.sqrt(mean_squared_error(df_temp['obs'], df_temp['pred']))
    
    # 3. R-squared (R2)
    # Note: r2_score can be negative if the model is arbitrarily worse than horizontal line
    r2 = r2_score(df_temp['obs'], df_temp['pred'])
    
    # 4. Bias (Mean Error = Mean Predicted - Mean Observed)
    # Positive bias means model overestimates
    bias = df_temp['pred'].mean() - df_temp['obs'].mean()
    
    return r, rmse, r2, bias

# =================================================
# 3. PROCESSING FUNCTIONS
# =================================================

def process_rc_cb_site(sap_file, inventory_code, flux_subpath, area_m2):
    """Process Robson Creek or Cow Bay using the Excel/Inventory scaling method."""
    print(f"Processing {inventory_code}...")
    
    # A. Load Sap Flux & Inventory
    sap_path = os.path.join(BASE_SAP_RC_CB, sap_file)
    inv_path = os.path.join(BASE_SAP_RC_CB, 'RC_and_CB_inventory_data.csv')
    
    df_sap = pd.read_excel(sap_path, engine='openpyxl')
    df_inv = pd.read_csv(inv_path)

    # Time Index
    time_col = df_sap.columns[0]
    df_sap[time_col] = pd.to_datetime(df_sap[time_col])
    df_sap.set_index(time_col, inplace=True)

    # Scale Sap Flux
    inv_site = df_inv[df_inv['Site'] == inventory_code]
    c_plot_total = (inv_site['DBH'] * np.pi).sum()
    
    # Scaling: Median Rate (kg/cm/hr) * Total Circ (cm) * 1 / Area (m2)
    t_plot_mm_hr = (df_sap.median(axis=1) * c_plot_total) / area_m2
    t_daily_sap = t_plot_mm_hr.resample('D').sum()

    # B. Load Flux Tower
    flux_path = os.path.join(BASE_FLUX_RC_CB, flux_subpath)
    if not os.path.exists(flux_path): flux_path = flux_path.replace('/fs04', '')
    
    df_flux = pd.read_csv(flux_path)
    df_flux['time'] = pd.to_datetime(df_flux['time'])
    df_flux.set_index('time', inplace=True)

    # Convert Units (W/m2 -> mm/day)
    flux_obs = (df_flux['LE_Obs'] * SECONDS_IN_DAY) / LHV
    flux_base = (df_flux['Base_LE_canopy'] * SECONDS_IN_DAY) / LHV
    flux_sm = (df_flux['SM_LE_canopy'] * SECONDS_IN_DAY) / LHV

    return pd.DataFrame({
        'SapFlux': t_daily_sap,
        'ET_Obs': flux_obs.resample('D').mean(),
        'Base': flux_base.resample('D').mean(),
        'SM': flux_sm.resample('D').mean()
    }).dropna()

def process_wombat_site():
    """Process Wombat State Forest using the SapFluxNet CSV method."""
    print("Processing Wombat...")
    
    # A. Load Sap Flux
    sapf_path = os.path.join(BASE_SAP_WOM, "AUS_WOM_sapf_data.csv")
    plant_path = os.path.join(BASE_SAP_WOM, "AUS_WOM_plant_md.csv")
    
    sap = pd.read_csv(sapf_path)
    plants = pd.read_csv(plant_path)

    sap["TIMESTAMP"] = pd.to_datetime(sap["TIMESTAMP"], utc=True)
    sap = sap.set_index("TIMESTAMP").sort_index()
    sap = sap.loc["2013-01-01":"2015-10-31"]

    # Cleaning & Scaling
    sap_cols = [c for c in sap.columns if "Js" in c]
    sap[sap_cols] = sap[sap_cols].where((sap[sap_cols] >= 0) & (sap[sap_cols] <= 60))
    
    sapwood_area = plants.set_index("pl_code")["pl_sapw_area"][sap_cols]
    total_sapwood_cm2 = sapwood_area.sum()
    
    # Calculate Volume -> Velocity -> Transpiration
    tree_vol = sap[sap_cols] * sapwood_area * 0.5 # dt_hours
    daily_vol = tree_vol.resample("D").sum().sum(axis=1)
    stand_velocity = (daily_vol / total_sapwood_cm2) * 10
    
    SAI = 0.001
    t_daily_sap = stand_velocity * SAI
    
    # Remove TZ for merging
    t_daily_sap.index = t_daily_sap.index.tz_localize(None)

    # B. Load Flux Tower
    flux_path = os.path.join(BASE_FLUX_WOM, "WombatStateForest1_PTJPLSM_v2.csv")
    if not os.path.exists(flux_path): flux_path = flux_path.replace('/fs04', '')
    
    ft = pd.read_csv(flux_path)
    ft["time"] = pd.to_datetime(ft["time"])
    ft = ft.set_index("time").sort_index()
    ft = ft.loc["2013-01-01":"2015-10-31"]
    
    # Units (Using the fixed constant)
    flux_obs = ft["LE_Obs"] * W_M2_TO_MM_DAY
    flux_sm = ft["SM_LE_canopy"] * W_M2_TO_MM_DAY
    flux_base = ft["Base_LE_canopy"] * W_M2_TO_MM_DAY

    return pd.DataFrame({
        'SapFlux': t_daily_sap,
        'ET_Obs': flux_obs,
        'Base': flux_base,
        'SM': flux_sm
    }).dropna()

# =================================================
# 4. PLOTTING FUNCTION (CORRECTED)
# =================================================
def plot_site(ax, df, site_name, show_legend=False):
    # Colors
    col_obs = '#999999'       # Light Grey (Context)
    col_base = '#d95f02'      # Vermilion/Orange (Base)
    col_sm = '#1b9e77'        # Teal/Green (SM - New)
    col_sap = '#00468b'       # Strong Blue (Sap Flux)

    # 1. Flux Tower Total ET (Background)
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

    # Stats: R, RMSE, R2, Bias
    r_sm, rmse_sm, r2_sm, bias_sm = calculate_metrics(df['SapFlux'], df['SM'])
    r_base, rmse_base, r2_base, bias_base = calculate_metrics(df['SapFlux'], df['Base'])
    
    # Format Text Box
    # Using compact notation for space
    stats_text = (
        f"$\\bf{{PT-JPL-SM}}$\n"
        f"$r={r_sm:.2f}$, $R^2={r2_sm:.2f}$\n"
        f"RMSE={rmse_sm:.2f}, Bias={bias_sm:.2f}\n\n"
        f"$\\bf{{Base}}$\n"
        f"$r={r_base:.2f}$, $R^2={r2_base:.2f}$\n"
        f"RMSE={rmse_base:.2f}, Bias={bias_base:.2f}"
    )
    
    ax.text(0.02, 0.95, stats_text, transform=ax.transAxes, fontsize=9,
            verticalalignment='top', bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=5))

    if show_legend:
        ax.legend(frameon=False, loc='upper right', fontsize=9, ncol=4)

# =================================================
# 5. MAIN EXECUTION
# =================================================

# Prepare Data
df_rc = process_rc_cb_site("Robson_Creek_Sap_flux_data.xlsx", "RC", "robsoncreek/RobsonCreek_PTJPLSM_v2.csv", 250000)
df_cb = process_rc_cb_site("Cow_Bay_Sap_flux_data.xlsx", "CB", "cowbay/CowBay_PTJPLSM_v2.csv", 8000)
df_wom = process_wombat_site()

# Plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 14), sharey=False) # Increased height slightly for text

# Plot each site
plot_site(ax1, df_rc, "Robson Creek (Tropical Rainforest)", show_legend=True)
plot_site(ax2, df_cb, "Cow Bay (Tropical Rainforest)", show_legend=False)
plot_site(ax3, df_wom, "Wombat State Forest (Dry Sclerophyll)", show_legend=False)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(hspace=0.3)
plt.show()

# Print Means for sanity check
print(f"\nMean Sap Flow - RC: {df_rc['SapFlux'].mean():.2f}, CB: {df_cb['SapFlux'].mean():.2f}, WOM: {df_wom['SapFlux'].mean():.2f}")
