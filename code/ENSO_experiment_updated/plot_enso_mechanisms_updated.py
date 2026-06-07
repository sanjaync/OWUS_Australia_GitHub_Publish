import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

try:
    from adjustText import adjust_text
    HAS_ADJUST_TEXT = True
except ImportError:
    HAS_ADJUST_TEXT = False

# Configuration & Aesthetics
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams.update({
    "font.family": "sans-serif",
    "axes.titleweight": "bold",
    "axes.labelweight": "bold",
    "figure.figsize": (10, 8),
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

INPUT_CSV = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/ENSO_experiment_updated/enso_results_summary.csv'
OUTPUT_DIR = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/ENSO_experiment_updated/plots_v2'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load Data
df = pd.read_csv(INPUT_CSV)

# Pivot Tables for Analysis
pivoted = df.pivot(index='Site', columns='Phase')
joined = pivoted.dropna() # Only sites with both phases

# Extract Series
pi_la = joined[('Pi_F', 'LaNina')]
pi_el = joined[('Pi_F', 'ElNino')]
rain_la = joined[('Rain', 'LaNina')]
rain_el = joined[('Rain', 'ElNino')]
s_star_la = joined[('S_star', 'LaNina')]
s_star_el = joined[('S_star', 'ElNino')]

# Calculate Shifts (El Nino [Dry] - La Nina [Wet])
shift_pi = pi_el - pi_la
mean_rain = (rain_la + rain_el) / 2

# =============================================================================
# PLOT 1: Rainfall vs Shift in Strategy (Baseline Climate Dictates Adaptation)
# =============================================================================
fig, ax = plt.subplots(figsize=(11, 8))

# Scatter points with color mapping based on shift direction
colors = ['#D62728' if y > 0 else '#1F77B4' for y in shift_pi]
scatter = ax.scatter(mean_rain, shift_pi, c=colors, s=180, edgecolor='white', linewidth=1.5, zorder=5, alpha=0.85)

# Add Labels
texts = []
for site in joined.index:
    texts.append(ax.text(mean_rain[site], shift_pi[site], site, fontsize=10, alpha=0.9, weight='medium'))

if HAS_ADJUST_TEXT:
    adjust_text(texts, arrowprops=dict(arrowstyle="-", color='gray', lw=0.5))
else:
    for t in texts:
        t.set_position((t.get_position()[0], t.get_position()[1] + 0.15))
        t.set_ha('center')

# Add Trendline
z = np.polyfit(mean_rain, shift_pi, 1)
p = np.poly1d(z)
x_trend = np.linspace(mean_rain.min()-100, mean_rain.max()+100, 100)
ax.plot(x_trend, p(x_trend), color="#333333", linestyle="--", linewidth=2.5, alpha=0.6, label='Linear Trend', zorder=3)

# Reference line
ax.axhline(0, color='black', linestyle=':', linewidth=1.5, alpha=0.5, zorder=1)

# Formatting
ax.set_xlabel('Mean Annual Rainfall (mm/yr)', fontsize=14)
ax.set_ylabel(r'Shift in Hydraulic Cost $\Delta\Pi_F$ (El Niño - La Niña)', fontsize=14)
ax.set_title('Does Baseline Climate Determine Drought Strategy?', fontsize=16, pad=20)
ax.set_xlim(left=0, right=mean_rain.max()*1.1)

# Pad y-axis heavily to make room for boxes
y_min, y_max = shift_pi.min(), shift_pi.max()
y_range = y_max - y_min
ax.set_ylim(y_min - y_range*0.3, y_max + y_range*0.4)

# Annotations for interpretation (moved out of the way)
ax.text(0.97, 0.95, "Wetter Sites\nBecome SAFER\n(Increase $\Pi_F$)", 
        transform=ax.transAxes, color='#D62728', fontsize=13, weight='bold', va='top', ha='right',
        bbox=dict(facecolor='white', alpha=0.9, edgecolor='#D62728', boxstyle='round,pad=0.5'))

# Moving this to the right side where there are no data points with negative shift
ax.text(0.97, 0.05, "Drier Sites\nBecome RISKIER\n(Decrease $\Pi_F$)", 
        transform=ax.transAxes, color='#1F77B4', fontsize=13, weight='bold', va='bottom', ha='right',
        bbox=dict(facecolor='white', alpha=0.9, edgecolor='#1F77B4', boxstyle='round,pad=0.5'))

sns.despine()
fig.savefig(os.path.join(OUTPUT_DIR, 'ENSO_Mechanism_1_Rainfall_vs_Shift_Updated.png'))
print(f"Saved: ENSO_Mechanism_1_Rainfall_vs_Shift_Updated.png")
plt.close()

# =============================================================================
# PLOT 2: Vector Trajectories (Dynamic Adaptation in Parameter Space)
# =============================================================================
fig, ax = plt.subplots(figsize=(11, 9))

texts = []
for site in joined.index:
    # Start (La Nina - Wet)
    x1, y1 = s_star_la[site], pi_la[site]
    # End (El Nino - Dry)
    x2, y2 = s_star_el[site], pi_el[site]
    
    # Color logic: Red if getting safer (Pi_F increases), Blue if getting riskier
    color = '#D62728' if y2 > y1 else '#1F77B4'
    
    # Arrow
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>,head_length=0.8,head_width=0.4",
                                color=color, lw=2.5, alpha=0.7), zorder=2)
    
    # Scatter points at start and end
    ax.scatter(x1, y1, color='gray', s=50, alpha=0.5, zorder=3)
    ax.scatter(x2, y2, color=color, s=80, edgecolor='white', zorder=4)
    
    # Label at the end of the arrow
    texts.append(ax.text(x2, y2, site, fontsize=10, color='#333333', weight='bold'))

if HAS_ADJUST_TEXT:
    adjust_text(texts, force_points=1.5, force_text=1.5, arrowprops=dict(arrowstyle="-", color='gray', lw=0.5))
else:
    for t in texts:
        t.set_position((t.get_position()[0], t.get_position()[1] + 0.1))
        t.set_ha('center')

# Legend
custom_lines = [Line2D([0], [0], color='#D62728', lw=3, marker='>'),
                Line2D([0], [0], color='#1F77B4', lw=3, marker='>')]
ax.legend(custom_lines, ['Shift to Safer Strategy (+)', 'Shift to Riskier Strategy (-)'], 
          loc='upper right', frameon=True, shadow=True)

ax.set_xlabel('Stomatal Sensitivity Target ($s^*$)', fontsize=14)
ax.set_ylabel('Hydraulic Cost Parameter ($\Pi_F$)', fontsize=14)
ax.set_title('Dynamic Trajectories: Wet $\\rightarrow$ Dry Adaptation', fontsize=16, pad=20)
sns.despine()

fig.savefig(os.path.join(OUTPUT_DIR, 'ENSO_Mechanism_2_Vector_Trajectories_Updated.png'))
print(f"Saved: ENSO_Mechanism_2_Vector_Trajectories_Updated.png")
plt.close()

# =============================================================================
# PLOT 3: Paired NSE Comparison (Performance Shift)
# =============================================================================
fig, ax = plt.subplots(figsize=(9, 9))

nse_la = joined[('NSE', 'LaNina')]
nse_el = joined[('NSE', 'ElNino')]
nse_diff = nse_el - nse_la

# Color palette: Green if El Nino performs better, Purple if La Nina performs better
colors = ['#2CA02C' if d > 0 else '#9467BD' for d in nse_diff]

ax.scatter(nse_la, nse_el, c=colors, s=200, edgecolors='white', linewidths=1.5, alpha=0.85, zorder=5)

# 1:1 Line
ax.plot([-1, 1.5], [-1, 1.5], color='black', linestyle='--', linewidth=2, alpha=0.6, label='1:1 Line', zorder=2)

# Shade lower right triangle (where La Nina > El Nino)
lim = [0.0, 1.1]
ax.fill_between(lim, [-1, -1], lim, color='#9467BD', alpha=0.08, zorder=1)
# Shade upper left triangle (where El Nino > La Nina)
ax.fill_between(lim, lim, [1.5, 1.5], color='#2CA02C', alpha=0.08, zorder=1)

texts = []
for site in joined.index:
    texts.append(ax.text(nse_la[site], nse_el[site], site, fontsize=10, weight='medium', alpha=0.9))

if HAS_ADJUST_TEXT:
    adjust_text(texts, force_points=1.5, force_text=1.5, arrowprops=dict(arrowstyle="-", color='gray', lw=0.5))
else:
    for t in texts:
        t.set_position((t.get_position()[0], t.get_position()[1] + 0.025))
        t.set_ha('center')

ax.set_xlabel('La Niña NSE (Wet Years)', fontsize=14)
ax.set_ylabel('El Niño NSE (Dry Years)', fontsize=14)
ax.set_title('Model Predictability Drops During Droughts', fontsize=16, pad=20)
ax.set_xlim(lim)
ax.set_ylim(lim)

# Quadrant Text - Moved deep into the corners to avoid overlapping points
ax.text(0.2, 0.8, 'Better Performance\nin Drought (El Niño)', color='#2CA02C', 
        fontsize=12, weight='bold', ha='center', va='center')
ax.text(0.8, 0.2, 'Better Performance\nin Wet (La Niña)', color='#9467BD', 
        fontsize=12, weight='bold', ha='center', va='center')

sns.despine()
fig.savefig(os.path.join(OUTPUT_DIR, 'ENSO_Mechanism_3_Performance_Shift.png'))
print(f"Saved: ENSO_Mechanism_3_Performance_Shift.png")
plt.close()

# =============================================================================
# PLOT 4: Directional Shift Bar Chart (Plasticity Direction)
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 9))

joined['Shift'] = shift_pi
joined_sorted = joined.sort_values('Shift')

# Diverging colors based on shift magnitude
import matplotlib.colors as mcolors
norm = mcolors.TwoSlopeNorm(vmin=joined_sorted['Shift'].min(), vcenter=0, vmax=joined_sorted['Shift'].max())
cmap = sns.diverging_palette(250, 15, s=90, l=50, n=256, as_cmap=True)
colors = [cmap(norm(val)) for val in joined_sorted['Shift']]

bars = ax.barh(joined_sorted.index, joined_sorted['Shift'], color=colors, edgecolor='white', linewidth=1)

# Formatting
ax.axvline(0, color='black', linewidth=1.5, zorder=0)
ax.set_xlabel(r'Change in Hydraulic Cost $\Delta\Pi_F$ (El Niño - La Niña)', fontsize=14)
ax.set_title(r'Plasticity Direction: Safer (+) vs Riskier (-) in Drought', fontsize=16, pad=20)

# Add values to bars
for i, bar in enumerate(bars):
    val = bar.get_width()
    offset = 0.15 if val > 0 else -0.15
    ha = 'left' if val > 0 else 'right'
    ax.text(val + offset, bar.get_y() + bar.get_height()/2, f'{val:+.2f}', 
            va='center', ha=ha, fontsize=10, weight='bold', color='#333333')

# Annotations
xlims = ax.get_xlim()
# Add padding so text fits
ax.set_xlim(xlims[0] - 1, xlims[1] + 1)
xlims = ax.get_xlim()

ax.text(xlims[0]*0.9, len(joined_sorted)*0.95, 'Riskier\nLess Constrained (-)', 
         color='#1F77B4', alpha=0.9, ha='left', va='top', fontweight='bold', fontsize=13)
ax.text(xlims[1]*0.9, 0.5, 'Safer\nMore Constrained (+)', 
         color='#D62728', alpha=0.9, ha='right', va='bottom', fontweight='bold', fontsize=13)

sns.despine(left=True)
ax.xaxis.grid(True, linestyle='--', alpha=0.5)
ax.yaxis.grid(False)
fig.savefig(os.path.join(OUTPUT_DIR, 'PiF_Directional_Shift_Updated.png'))
print(f"Saved: PiF_Directional_Shift_Updated.png")
plt.close()

print("All enhanced publication-quality plots generated successfully.")

