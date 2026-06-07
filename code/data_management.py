import sys 
import os
import numpy as np
from pandas import date_range
import pandas as pd
import xarray as xr
from datetime import datetime


Mw = 0.018          # [kg mol-1] Molar mass of water          
rho_w = 1000        # [kg m-3] Density of liquid water
mwratio = 0.622     # - Ratio molecular weight of water vapor/dry air
cp_air = 1005       # J/kg/k specific heat of air
Lv = 2.5008 * 10**6 # (J/kg) is the latent heat of vaporization of water

drive_w = '/Volumes/SLU_maoya/E'

sites_params = pd.read_csv('/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_2/sanjay data creation/master_files/pedo_master_file.csv')
pft_params = pd.read_csv('/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_2/sanjay data creation/master_files/selected_pft_params_refs.csv')

def get_site_params_from_master(site_id):
    """Extract soil parameters directly from the master CSV."""
    df_p = sites_params[sites_params['siteID'] == site_id]
    if df_p.empty:
        raise ValueError(f"Site {site_id} not found in master file.")
    
    # Map from master file columns to expected names
    row = df_p.iloc[0]
    MAXSMC = row['MAXSMC']
    DRYSMC = row['DRYSMC']
    BB = row['BB']
    SATPSI = row['SATPSI'] * -9.8067 * 10 ** -3 # m to MPa (assuming it was in m)
    SATDK = row['SATDK'] # m s-1
    return BB, SATPSI, SATDK, MAXSMC, DRYSMC

def get_site_data_ozflux(site_id):
    """Load OzFlux NetCDF data and map to OWUS variables."""
    df_p = sites_params[sites_params['siteID'] == site_id]
    if df_p.empty:
        return None
    
    nc_path = df_p['nc_file_path'].values[0]
    lai_fpar_path = df_p['lai_fpar_file_path'].values[0]
    swc_var_str = df_p['swc_i'].values[0]  # Get SWC variable name(s) from master file
    
    print(f"Loading NetCDF: {nc_path}")
    ds = xr.open_dataset(nc_path)
    
    # Flatten spatial dims since it's 1x1
    ds = ds.squeeze(['latitude', 'longitude'])
    
    # Define variables to load
    base_vars = ['Precip', 'Ta', 'VPD', 'GPP_SOLO', 'Fe', 'Fh']
    
    # Initialize df with time index
    df = pd.DataFrame(index=ds['time'].to_pandas())
    
    def apply_quality_control(ds, var_name, series):
        """Filter series based on NetCDF valid_range and QC flags."""
        if var_name not in ds:
            return series
            
        da = ds[var_name]
        
        # 1. Enforce Hard Limits (Safety Net)
        # Soil Moisture must be [0, 1]
        if var_name in ['Sws', 'SWC', 'Sws_20cm', 'Sws_40cm'] or 'Sws' in var_name:
            # Clip values
            series = series.clip(lower=0.0, upper=1.0)
        
        # Precip/Rainfall must be >= 0
        if var_name in ['Precip', 'RF', 'Rain']:
            series[series < 0] = 0.0

        # 2. QC Flag Filter
        # Filter out bad quality data if QC flag exists
        qc_var = f"{var_name}_QCFlag"
        if qc_var in ds:
            try:
                qc_vals = ds[qc_var].to_series()
                # Align indices (important if series was resampled or shifted, though here it's raw)
                qc_aligned = qc_vals.reindex(series.index)
                
                # Flag Logic: 0 = Measured (Good), 10 = High Conf Gapfill (Good)
                # 20, 30, 40, 50, etc. often imply lower confidence or specific issues
                # We filter out anything > 10 to be safe, or >20 depending on strictness.
                # OzFlux: 00=measured, 10=gapfilled (good), 20=gapfilled (fair), 30=gapfilled (poor)
                # Let's keep 0 and 10.
                # Relax QC for Precip/RF as it might come from external sources with high flags (e.g. 410)
                threshold = 500 if var_name in ['Precip', 'RF', 'Rain'] else 10
                mask_bad = (qc_aligned > threshold) 
                
                if mask_bad.any():
                    n_bad = mask_bad.sum()
                    # print(f"  [{var_name}] QC Filter: Removed {n_bad} points (Flag > 10)")
                    series[mask_bad] = np.nan
            except Exception as e:
                print(f"  [{var_name}] QC check failed: {e}")

        # 3. Valid Range Filter (from Attributes)
        # Keep this as a secondary check, but rely on hard limits above for physics
        if 'valid_range' in da.attrs:
            vr = da.attrs['valid_range']
            try:
                if len(vr) == 2:
                    vmin, vmax = vr[0], vr[1]
                    # Don't re-apply if we already hard clipped (unless attr is tighter)
                    mask_out = (series < vmin) | (series > vmax)
                    if mask_out.any():
                        n_rem = mask_out.sum()
                        # print(f"  [{var_name}] Attr Filter: {n_rem} outside [{vmin}, {vmax}]")
                        series[mask_out] = np.nan
            except Exception as e:
                print(f"  [{var_name}] Failed to parse valid_range: {e}")
                
        return series

    # Load and filter base variables
    for v in base_vars:
        if v in ds:
            s = ds[v].to_series()
            s = apply_quality_control(ds, v, s)
            df[v] = s
    
    # Handle single or multiple SWC variables
    # Parse swc_var_str which may contain comma-separated variable names
    swc_vars = [v.strip() for v in swc_var_str.replace(' ', '').split(',') if v.strip()]
    if len(swc_vars) == 0:
        swc_vars = ['Sws']  # Default fallback
    
    # Check which variables actually exist in the dataset
    valid_swc_vars = [v for v in swc_vars if v in ds.data_vars]
    if len(valid_swc_vars) == 0:
        # Try default 'Sws' if specified vars not found
        if 'Sws' in ds.data_vars:
            valid_swc_vars = ['Sws']
        else:
            print(f"WARNING: No valid SWC variables found for {site_id}. Available: {list(ds.data_vars)}")
            return None
    
    print(f"Using SWC variable(s): {valid_swc_vars}")
    
    # Process SWC variables
    swc_series_list = []
    for v in valid_swc_vars:
        s = ds[v].to_series()
        s = apply_quality_control(ds, v, s)
        swc_series_list.append(s)

    # Average multiple SWC sensors if present
    if len(swc_series_list) == 1:
        df['Sws'] = swc_series_list[0]
    else:
        # Average multiple sensors (ignoring NaNs from filtering)
        combined = pd.concat(swc_series_list, axis=1)
        df['Sws'] = combined.mean(axis=1)
        print(f"  Averaged {len(valid_swc_vars)} SWC sensors")
    
    # Conversion: VPD kPa -> Pa
    if 'VPD' in df:
        df['VPD_air'] = df['VPD'] * 1000.
    
    # Conversion: Ta -> T_air
    if 'Ta' in df:
        df['T_air'] = df['Ta']
    
    # Conversion: Precip mm -> m/day (assuming 30min timestep, so sum it or handle daily)
    # The code usually resamples to DD later, but we need 'RF' in m/day.
    # If we convert to m per timestep, resample('D').sum() gives m/day.
    if 'Precip' in df:
        df['RF'] = df['Precip'] / 1000. 
    
    # Conversion: GPP_SOLO umol/m2/s -> mol/m2/s
    if 'GPP_SOLO' in df:
        df['GPP'] = df['GPP_SOLO'] * 1e-6
    
    # Soil Water Content
    if 'Sws' in df:
        df['SWC'] = df['Sws']
    
    # Energy fluxes for PET calculation
    # Check if Fe/Fh exist (might be missing if excluded by var check)
    if 'Fe' in df and 'Fh' in df:
        df['Qn'] = df['Fe'] + df['Fh'] # Simplified Qn if Fn missing, but Fn is usually there
    
    if 'Fn' in ds:
        s_fn = ds['Fn'].to_series()
        s_fn = apply_quality_control(ds, 'Fn', s_fn)
        df['Qn_raw'] = s_fn
        df['Qn'] = df['Qn_raw']
        
    # ET observations
    # Fe is in W/m² (average rate), statistic_type='average'
    # Convert to mm per 30-min timestep: ET = Fe × 1800s / Lv (J/kg)
    # Lv = 2.45e6 J/kg, so factor = 1800/2450000 = 0.000735 mm per 30-min per W/m²
    # Daily sum (48 timesteps) will give correct mm/day
    if 'Fe' in df:
        df['ET_obs_mol'] = df['Fe'] / Lv / Mw
        df['ET_obs_m'] = df['Fe'] * 1800 / Lv  # mm per 30-min (will be summed to mm/day, then /1000 for m/day)
    
    # Calculate ETo using existing functions but on NetCDF data
    # Note: atm_pressure (P_air) may be needed. Checking if 'ps' or 'P' exists.
    if 'ps' in ds:
        p_air = ds['ps'].to_series()
        p_air = apply_quality_control(ds, 'ps', p_air)
        df['P_air'] = p_air * 1000. # kPa to Pa
    else:
        df['P_air'] = 101325. # Default
        
    if 'Qn' in df and 'T_air' in df:
        df['LE_o'] = pt_ETo(df['Qn'], df['T_air'], df['P_air'])
        df['ETo_m'] = df['LE_o'] * 1800 / Lv  # mm per 30-min (will be summed to mm/day, then /1000 for m/day)
        df['ETo_mol'] = df['LE_o'] / Lv / Mw
    
    # LAI and fPAR from climatology file
    print(f"Loading Climatology: {lai_fpar_path}")
    df_clim = pd.read_csv(lai_fpar_path)
    # The climatology file usually has 'DOY' and the mean values
    # Map these back to the main dataframe's index
    df['DOY'] = df.index.dayofyear
    
    # Handle case-insensitive 'doy'
    doy_col = 'doy' if 'doy' in df_clim.columns else 'DOY'
    
    # Identify LAI and fPAR columns
    lai_col = next((c for c in ['LAI_smooth', 'LAI', 'lai_mean'] if c in df_clim.columns), df_clim.columns[1])
    fpar_col = next((c for c in ['FPAR_smooth', 'fpar', 'fpar_mean'] if c in df_clim.columns), df_clim.columns[2])
    
    print(f"Mapping {lai_col} and {fpar_col} from {doy_col}")
    lai_map = df_clim.set_index(doy_col)[lai_col].to_dict()
    fpar_map = df_clim.set_index(doy_col)[fpar_col].to_dict()
    
    df['LAI'] = df['DOY'].map(lai_map)
    df['fpar'] = df['DOY'].map(fpar_map)
    
    # Select final columns
    final_cols = ['RF', 'T_air', 'VPD_air', 'SWC', 'ET_obs_mol', 'ETo_mol', 'GPP', 'ET_obs_m', 'ETo_m', 'LAI', 'fpar']
    df = df[final_cols]
    
    # Resample to daily
    # RF and ET depths should be summed.
    # T_air, VPD, SWC, LAI, fpar should be averaged.
    # Note: GPP is umol/m2/s, mean daily * Td would give mol/day. 
    # But often we just want the mean daily GPP in mol/m2/s.
    
    agg_dict = {col: 'mean' for col in final_cols}
    agg_dict['RF'] = 'sum'
    agg_dict['ET_obs_m'] = 'sum'
    agg_dict['ETo_m'] = 'sum'
    
    df_daily = df.resample('D').agg(agg_dict).dropna()
    
    # Convert ET from mm/day to m/day for consistency with rest of codebase
    df_daily['ET_obs_m'] = df_daily['ET_obs_m'] / 1000  # mm/day → m/day
    df_daily['ETo_m'] = df_daily['ETo_m'] / 1000  # mm/day → m/day
    
    return df_daily

# Old functions like get_site_data_flx, insert_LAI etc can be kept or bypassed.
# We will use get_site_data_ozflux instead.

# Update get_site_params to use our new soil parameter extractor
def get_site_params_ozflux(site, data, data_0):
    if data.empty or data_0.empty:
        print(f"Skipping {site}: Empty data after processing.")
        return None
        
    df_p = sites_params[sites_params['siteID'] == site]
    row = df_p.iloc[0]
    
    params = {
        'siteID': site,
        'pft': row['pft_0'],
        'IGBP': row['IGBP'],
        'clim': row['climate'],
        'soil_tex_id': row['soil_tex_id'],
        'swc_i': row['swc_i'],
        'Zm': -row['Zm'], # Original site Zm
        'lat': row['lat'],
        'lon': row['lon'],
        'frac_H': row['frac_H'],
        'frac_T': row['frac_T'],
        'frac_B': row['frac_B'],
        'frac_V': row['frac_V'],
    }
    
    gs_days = list(set(data.index.dayofyear))
    td = [get_length_of_day(params['lat'], jd) for jd in gs_days]
    params['Td'] = np.ceil(np.nanmean(td) * 3600.)
    params['T_GS'] = len(gs_days)
    params['DOY_GS'] = gs_days
    
    # Climate characteristics
    params['Eo'] = np.nanmean(data['ETo_m'])
    params['D_mean'] = np.nanmean(data['VPD_air'])
    
    vpd_data = data['VPD_air'].dropna()
    if vpd_data.empty:
        params['D_peak'] = params['D_mean']
    else:
        params['D_peak'] = np.percentile(vpd_data, 95)
    
    rf_alpha, rf_lambda = stochastic_rf_char(data['RF'].values)
    params['rf_alpha'] = rf_alpha
    params['rf_lambda'] = rf_lambda
    params['RF_a'] = np.nanmean(data_0['RF'])
    params['RF'] = np.nanmean(data['RF'])
    
    params['AI_a'] = np.nanmean(data_0['ETo_m']) / np.nanmean(data_0['RF'])
    params['EF_a'] = np.nanmean(data_0['ET_obs_m']) / np.nanmean(data_0['RF'])
    params['AI'] = np.nanmean(data['ETo_m']) / np.nanmean(data['RF'])
    params['EF'] = np.nanmean(data['ET_obs_m']) / np.nanmean(data['RF'])
    params['GPP_mean'] = np.nanmean(data['GPP'])
    params['ET_mean'] = np.nanmean(data['ET_obs_m'])
    
    # Soil physical characteristics - Integrated from Master
    BB, SATPSI, SATDK, MAXSMC, DRYSMC = get_site_params_from_master(site)
    params['b'] = BB
    params['Ps0'] = SATPSI
    params['Ks'] = SATDK * params['Td']
    
    swcmax = np.ceil(np.nanmax(data_0['SWC']) * 100) / 100.
    params['n'] = swcmax
    data['S'] = data['SWC'] / params['n']
    data_0['S'] = data_0['SWC'] / params['n']
    
    if s_to_pot_BC(np.nanmin(data_0['S'].values), params['b'], params['Ps0']) < -10:
        params['b'] = (np.log(10) - np.log(-params['Ps0'])) / (np.log(1) - np.log(np.nanmin(data_0['S'].values)))
        
    sh = pot_to_s_BC(-10, params['b'], params['Ps0'])
    params['s_h'] = np.floor(sh * 100) / 100. - 0.01
    params['s_fc_ref'] = pot_to_s_BC(-0.03, params['b'], params['Ps0'])
    
    data_0['ds/dt'] = data_0['S'].diff()
    sm_peaks = [smi for dsi, smi in zip(data_0['ds/dt'].values, data_0['S'].values) if dsi > 0]
    s_fc_r = np.percentile(sm_peaks, 95) if sm_peaks else 0.5
    params['s_fc_rec'] = s_fc_r
    params['s_fc'] = np.max([params['s_fc_ref'], params['s_fc_rec']])
    
    # PFT parameters
    pft0 = row['pft']
    df_pft = pft_params[pft_params['PFT'] == pft0]
    if df_pft.empty: # Fallback
        df_pft = pft_params.iloc[0:1]
        
    params['Zr_m'] = df_pft['Zr_mean'].values[0]
    params['RAI'] = df_pft['RAI'].values[0]
    params['dr'] = 0.0005
    params['hc'] = get_fluxnet_hc_oz(site) # Need an OzFlux version of hc
    
    params['k_xl_max'] = df_pft['kl_max'].values[0]
    params['Px50'] = df_pft['Px50'].values[0]
    params['gs_max_ref'] = df_pft['g_max'].values[0]
    params['Pg50'] = -1.5
    
    params['LAI_s90'] = np.nanpercentile(data_0['LAI'], 90)
    params['LAI_s'] = np.nanmean(data['LAI'])
    params['LAI_v'] = params['LAI_s'] / params['frac_V']
    params['LAI'] = params['LAI_s']
    
    params['fpar_s90'] = np.nanpercentile(data_0['fpar'], 90)
    params['fpar_s'] = np.nanmean(data['fpar'])
    params['fpar_v'] = params['fpar_s'] / params['frac_V']
    params['fpar'] = params['fpar_s']
    
    params['s_obs'] = data['S'].dropna().values
    p_obs = np.histogramdd([params['s_obs']], [np.linspace(0, 1, 101)])[0]
    params['p_obs'] = p_obs / np.sum(p_obs)
    params['obs_l'] = [np.percentile(params['s_obs'], qi / 365. * 100) for qi in range(1, 365)]
    params['l_obs'] = len(params['s_obs'])
    params['nYear'] = len(list(set(data.index.year)))
    
    return params

def get_fluxnet_hc_oz(site):
    """Fallback for canopy height."""
    # This could be extracted from master if added, or hardcoded/looked up.
    # For now, return a default or site-specific value if known.
    return 10.0

def s_to_pot_BC(s, b, Ps0):
    psi = Ps0 * (s ** - b)  
    return psi

def pot_to_s_BC(psi, b, Ps0):
    s = (psi / Ps0) ** (- 1 / b)
    return s

def stochastic_rf_char(rf):
    mu = np.nanmean(rf)
    var = np.nanvar(rf)
    l = 2 * mu ** 2 / var
    a = mu / l
    return a, l

def psychrometric_cste(atm_pressure):
    # Pa/C
    return cp_air * atm_pressure / (Lv * mwratio)

def vapor_pressure_slope(air_temp):
    # Pa/C
    a =  np.exp((17.27 * air_temp) / (air_temp + 237.3)) 
    b = (air_temp + 237.3) ** 2
    delta = a / b * 2.504 * 10 ** 6 
    return delta

def pt_ETo(Qn, air_temp, atm_pressure):
    #preistley Taylor
    delta = vapor_pressure_slope(air_temp)
    pt = 1.26 * delta / (delta + psychrometric_cste(atm_pressure)) * Qn
    return pt

def get_length_of_day(latitude, jd):
    n = jd - 2451545
    l = 280.46 + 0.9856474 * n
    while l < 0 :
        l = l + 360
    while l > 360:
        l = l - 360
    g = 357.528 + 0.9856003 * n
    while g < 0 :
        g = g + 360
    while g > 360:
        g = g - 360

    ecliptic_lon = l + 1.915 * np.sin(g) + 0.02 * np.sin(2 * g)
    obliquity = 23.439 - 0.0000004 * n
    declination = np.arcsin(np.sin(obliquity) * np.sin(ecliptic_lon))

    lod = np.arccos(- np.tan(latitude) * np.tan(declination)) *  24 / np.pi
    if np.isnan(lod):
        lod = 12
    return lod

def select_growing_season(data, gpp_th=[95, 0.10], t_th=2, lai_th=None):
    # select growing season months
    if 'DOY' not in data.columns:
        data['DOY'] = data.index.dayofyear
    data['M'] = data.index.month
    data['Y'] = data.index.year
    data_doy = data[['GPP', 'LAI', 'T_air', 'DOY', 'M']].groupby('DOY').mean().dropna()
    data_m = data[['GPP', 'LAI', 'T_air', 'M']].groupby('M').mean().dropna()
    
    if lai_th is None:
        th_m =  np.percentile(data_m['GPP'].dropna(), gpp_th[0]) * gpp_th[1]
        data_m = data_m[(data_m['GPP'] >= th_m) & (data_m['T_air'] >= t_th) ]
        months_gs = list(data_m.index)
    else:
        th_m =  np.percentile(data_m['LAI'].dropna(), lai_th[0]) * lai_th[1]
        th_m = np.max([0.25, th_m])
        data_m = data_m[(data_m['LAI'] >= th_m) & (data_m['T_air'] >= t_th) ]
        months_gs = list(data_m.index)

    selected_days = [i for i in data.index if i.month in months_gs]
    data_gs = data.loc[selected_days]
    doy_gs = [dd for dd in data_doy['M'] if dd in months_gs]
    
    years = list(data_gs.index.year)
    data_gs = data_gs.resample('D').mean().dropna()
    
    # Calculate expected days in growing season months (not full year)
    from calendar import monthrange
    gs_days_expected = sum(monthrange(2020, m)[1] for m in months_gs) if months_gs else 365
    
    # Exception for short-record sites: if total data < 1 year, reduce threshold to 40%
    total_data_days = len(data)
    year_threshold = 0.8 if total_data_days >= 365 else 0.4
    
    for y in years:
        ll = len(data_gs[data_gs['Y'] == y].dropna().index)
        # Require threshold % of GROWING SEASON days, not all 365 days
        if ll < year_threshold * gs_days_expected:
            data_gs = data_gs[data_gs['Y'] != y]

    return data_gs, doy_gs

if __name__ == "__main__":
    pass
