import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.patches import Rectangle, FancyArrowPatch, Ellipse, Circle
import re
import os
import gc  # Garbage collection for memory management
import textwrap
import warnings

# ------------------------------------------------------------------------------
# Silence noisy warnings
# ------------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=RuntimeWarning, module="matplotlib.patches")
warnings.filterwarnings("ignore", category=UserWarning, module="cartopy.mpl.feature_artist")
warnings.filterwarnings("ignore", category=UserWarning, module="pyproj")  # Silence the pyproj warning

# --- IMPORTS FOR MAPPING ---
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False

# ==============================================================================
# 1. CONFIGURATION & JOURNAL STYLING
# ==============================================================================
INPUT_FILE = "/fs04/scratch2/et97/oldscratch/Ozflux_data_full/L6/soil_depth_plots/OzFlux_Sws_Metadata_Filtered.xlsx"
OUTPUT_BASE_DIR = "FluxTower_Diagrams"

# Journal Style Settings
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Helvetica']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['figure.max_open_warning'] = 0 # Disable max figure warning

X_LIMIT = 45
TEXT_OFFSET_X = 22
LABEL_BUFFER = 25
LABEL_MARGIN_BOTTOM = 40

SENSOR_COLORS = ["#1B5E20", "#0D47A1", "#BF360C", "#4A148C", "#006064", "#424242"]

# ==============================================================================
# 2. DRAWING FUNCTIONS
# ==============================================================================
def get_soil_color_palette(soil_desc):
    return ["#D7CCC8", "#5D4037"] 

def format_sensor_label(var_name, depth_m):
    return str(var_name)

def draw_flux_tower(ax, meta, plot_scale):
    tower_h_m = meta.get("val_tower_h", 15.0)
    if tower_h_m is None or pd.isna(tower_h_m) or tower_h_m <= 0:
        return

    tower_plot_h = tower_h_m * plot_scale
    base_w, top_w = 3.0, 1.0

    ax.plot([-base_w/2, -top_w/2], [0, tower_plot_h], color="#263238", lw=2.0, zorder=3)
    ax.plot([base_w/2, top_w/2], [0, tower_plot_h], color="#263238", lw=2.0, zorder=3)

    levels = 8
    h_steps = np.linspace(0, tower_plot_h, levels+1)
    for i in range(levels):
        y1, y2 = h_steps[i], h_steps[i+1]
        w1 = base_w - (base_w - top_w) * (y1 / tower_plot_h)
        w2 = base_w - (base_w - top_w) * (y2 / tower_plot_h)
        ax.plot([-w1/2,  w2/2], [y1, y2], color="#78909C", lw=0.8, zorder=2)
        ax.plot([ w1/2, -w2/2], [y1, y2], color="#78909C", lw=0.8, zorder=2)
        ax.plot([-w1/2, w1/2], [y1, y1], color="#263238", lw=1.2, zorder=3)

    boom_heights = [tower_plot_h * 0.85, tower_plot_h * 0.55]
    for h in boom_heights:
        ax.plot([-base_w*1.2, base_w*1.2], [h, h], color="#263238", lw=1.5, zorder=3)
        ax.add_patch(Rectangle((-base_w*1.2 - 1, h - 0.5), 1, 1, color="#455A64", zorder=4))
        ax.add_patch(Rectangle(( base_w*1.2,        h - 0.5), 1, 1, color="#455A64", zorder=4))

    ax.plot([0, 0], [tower_plot_h, tower_plot_h + 5], color="#263238", lw=1.5, zorder=3)
    sonic_y = tower_plot_h + 4
    ax.plot([-1.5, 1.5], [sonic_y, sonic_y], color="#263238", lw=1.2, zorder=4)
    ax.add_patch(Rectangle((-1.7, sonic_y-0.5), 0.4, 1, color="#78909C", zorder=5))
    ax.add_patch(Rectangle(( 1.3, sonic_y-0.5), 0.4, 1, color="#78909C", zorder=5))
    ax.add_patch(Rectangle((-0.5, sonic_y+1),    1.0, 0.5, color="#78909C", zorder=5))

    site_name = meta.get("site_name") or "Flux tower"
    flux_id = meta.get("fluxnet_id")
    if flux_id is not None and not (isinstance(flux_id, float) and pd.isna(flux_id)):
        line1 = f"{site_name} ({flux_id})"
    else:
        line1 = f"{site_name}"
    label_text = f"{line1}\nFlux tower height: {tower_h_m:.1f} m"

    ax.text(0, tower_plot_h + 6, label_text, ha="center", va="bottom",
            fontsize=9, fontweight="bold", color="#263238", zorder=20)

def draw_eddies(ax, y_max_sky):
    eddy_configs = [
        {'x': -X_LIMIT*0.6, 'y': y_max_sky * 0.25, 'size': 15, 'rad': 0.5,  'style': 'arc3,rad=0.5'},
        {'x':  X_LIMIT*0.5, 'y': y_max_sky * 0.45, 'size': 18, 'rad': -0.4, 'style': 'arc3,rad=-0.4'},
        {'x': -X_LIMIT*0.3, 'y': y_max_sky * 0.65, 'size': 12, 'rad': 0.3,  'style': 'arc3,rad=0.3'}
    ]
    for cfg in eddy_configs:
        ax.add_patch(FancyArrowPatch((cfg['x'], cfg['y']), (cfg['x'] + cfg['size']/2, cfg['y'] + cfg['size']/2),
            arrowstyle='->', connectionstyle=cfg['style'], mutation_scale=15,
            color='#B0BEC5', alpha=0.6, lw=1.0, zorder=1))

def draw_canopy_strip(ax, meta, y_max_sky, plot_scale):
    canopy_h_m = meta.get("val_canopy_h", None)
    if canopy_h_m is None or pd.isna(canopy_h_m) or canopy_h_m <= 0:
        return

    h_plot = canopy_h_m * plot_scale
    x_center = X_LIMIT - 5.0

    if canopy_h_m < 2.0:
        bush_w = max(4.0, h_plot * 1.5)
        ax.add_patch(Ellipse((x_center, h_plot * 0.4), width=bush_w, height=h_plot * 0.9,
            facecolor="#C5E1A5", edgecolor="#33691E", lw=1.0, zorder=5))
        label_color = "#33691E"
    else:
        trunk_w = 1.2
        trunk_h = min(h_plot * 0.3, 6.0)
        if trunk_h >= h_plot: trunk_h = h_plot * 0.6
        crown_h = h_plot - trunk_h
        crown_w = min(crown_h * 0.7 + 3.0, 8.0)
        ax.add_patch(Rectangle((x_center - trunk_w/2, 0), trunk_w, trunk_h,
            facecolor="#8D6E63", edgecolor="#4E342E", lw=1, zorder=4))
        ax.add_patch(Ellipse((x_center, trunk_h + crown_h / 2.0), width=crown_w * 0.9, height=crown_h,
            facecolor="#A5D6A7", edgecolor="#2E7D32", lw=1.0, zorder=5))
        label_color = "#2E7D32"

    label_y = min(h_plot + 5, y_max_sky - 5)
    ax.text(x_center, label_y, f"Canopy\n({canopy_h_m:.1f} m)", ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=label_color, zorder=15)

    veg_type = meta.get("vegetation")
    if veg_type and pd.notna(veg_type) and str(veg_type).strip().lower() != "nan":
        display_veg = textwrap.fill(str(veg_type), width=20)
        ax.text(X_LIMIT - 2.0, 3, f"Veg: {display_veg}", fontsize=9, color="#1B5E20",
                va='bottom', ha='right', fontweight='bold', zorder=20,
                bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', pad=1))

def draw_scene(ax, y_min, y_max_sky, meta, plot_scale):
    soil_colors = get_soil_color_palette(meta.get("soil", ""))
    soil_grad = np.linspace(0, 1, 256).reshape(-1, 1)
    cmap_soil = mcolors.LinearSegmentedColormap.from_list("soil", soil_colors)
    ax.imshow(soil_grad, aspect='auto', cmap=cmap_soil, extent=[-X_LIMIT, X_LIMIT, y_min, 0], zorder=0, alpha=0.7)

    sky_grad = np.linspace(1, 0, 256).reshape(-1, 1)
    cmap_sky = mcolors.LinearSegmentedColormap.from_list("sky", ["#BBDEFB", "#E3F2FD"])
    ax.imshow(sky_grad, aspect='auto', cmap=cmap_sky, extent=[-X_LIMIT, X_LIMIT, 0, y_max_sky], zorder=0)

    draw_eddies(ax, y_max_sky)
    draw_flux_tower(ax, meta, plot_scale)
    draw_canopy_strip(ax, meta, y_max_sky, plot_scale)

    ax.axhline(0, color="#3E2723", lw=1.5, zorder=5)
    x_grass = np.linspace(-X_LIMIT, X_LIMIT, 400)
    y_grass = 0.8 * np.abs(np.sin(x_grass * 3)) + 0.2 * np.random.rand(400)
    ax.fill_between(x_grass, 0, y_grass, color="#7CB342", alpha=1.0, zorder=6)

def place_labels(ax, sdata, y_min_soil):
    sorted_data = sdata.sort_values("plot_y", ascending=False)
    cursor_left, cursor_right = -5, -5
    min_allowed_y = y_min_soil + LABEL_MARGIN_BOTTOM
    unique_depths = sorted(sdata['plot_y'].unique(), reverse=True)
    depth_to_color = {d: SENSOR_COLORS[i % len(SENSOR_COLORS)] for i, d in enumerate(unique_depths)}

    for i, row in sorted_data.iterrows():
        y_pos, label_text = row['plot_y'], row['label']
        x_pos, sensor_color = (-1.0 if i % 2 == 0 else 1.0), depth_to_color[y_pos]
        ax.scatter(x_pos, y_pos, color=sensor_color, edgecolors="white", linewidth=1.0, s=80, zorder=10)
        ax.axhline(y_pos, color=sensor_color, linestyle=":", linewidth=0.8, alpha=0.6, zorder=1)

        if i % 2 == 0:
            text_x = -TEXT_OFFSET_X
            target_y = max(min(y_pos, cursor_left), min_allowed_y)
            cursor_left = target_y - LABEL_BUFFER
            align_h, conn_angle = 'right', "angle,angleA=0,angleB=90,rad=5"
        else:
            text_x = TEXT_OFFSET_X
            target_y = max(min(y_pos, cursor_right), min_allowed_y)
            cursor_right = target_y - LABEL_BUFFER
            align_h, conn_angle = 'left', "angle,angleA=180,angleB=90,rad=5"

        ax.annotate(label_text, xy=(x_pos, y_pos), xytext=(text_x, target_y),
            textcoords='data', ha=align_h, va='center', fontsize=9, fontweight='bold', color="#212121",
            bbox=dict(boxstyle="square,pad=0.3", fc="white", alpha=0.9, ec=sensor_color, lw=0.9),
            arrowprops=dict(arrowstyle="-", linestyle="-", color=sensor_color, lw=1.0, shrinkB=5, alpha=0.8, connectionstyle=conn_angle),
            zorder=11)

def render_plot(meta, sdata, y_min_soil, y_max_sky, plot_scale, output_folder):
    # Ensure no interactive plotting
    plt.ioff()
    
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_ylim(y_min_soil, y_max_sky)
    ax.set_xlim(-X_LIMIT, X_LIMIT)

    draw_scene(ax, y_min_soil, y_max_sky, meta, plot_scale)
    if not sdata.empty:
        place_labels(ax, sdata, y_min_soil)

    def format_coord(y, pos):
        if y > 0: return f"+{y/plot_scale:.1f} m"
        elif y < 0: return f"{int(abs(y))} cm"
        else: return "0"

    ax.yaxis.set_major_formatter(FuncFormatter(format_coord))
    ax.yaxis.set_major_locator(MultipleLocator(50))
    ax.set_ylabel("Depth (−cm below ground)  |  Height (+m above ground)",
        fontsize=11, fontweight='bold', labelpad=10, color="#37474F")
    ax.set_xticks([])

    site = meta.get("site_name") or "Unknown Site"
    flux_id = meta.get("fluxnet_id")
    site_label = f"{site} ({flux_id})" if flux_id is not None and not (isinstance(flux_id, float) and pd.isna(flux_id)) else site
    
    info_lines = [f"Site: {site_label}"]
    if meta.get("period_str"): info_lines.append(f"Period: {meta['period_str']}")
    lat, lon = meta.get("latitude"), meta.get("longitude")
    if pd.notna(lat) and pd.notna(lon): info_lines.append(f"Lat: {lat:.3f}, Lon: {lon:.3f}")
    if pd.notna(meta.get("altitude")): info_lines.append(f"Elev: {int(meta['altitude'])} m a.s.l.")
    if pd.notna(meta.get("soil")): info_lines.append(f"Soil: {meta['soil']}")

    ax.text(0.02, 0.98, "\n".join(info_lines), transform=ax.transAxes, fontsize=10, va='top', ha='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='#90A4AE'))

    fig.subplots_adjust(top=0.95, right=0.96, bottom=0.05, left=0.1)

    # Cartopy map
    if CARTOPY_AVAILABLE and pd.notna(lat) and pd.notna(lon):
        try:
            pos = ax.get_position()
            map_w, map_h = 0.18, 0.15
            map_left = pos.x1 - map_w - 0.02
            map_bottom = pos.y1 - map_h - 0.02
            map_ax = fig.add_axes([map_left, map_bottom, map_w, map_h], projection=ccrs.PlateCarree())
            map_ax.set_extent([112, 154, -44, -10], crs=ccrs.PlateCarree())
            map_ax.add_feature(cfeature.LAND, facecolor='#EEEEEE')
            map_ax.add_feature(cfeature.OCEAN, facecolor='#FFFFFF')
            map_ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color='#607D8B')
            map_ax.plot(lon, lat, marker='o', color='#D32F2F', markersize=5,
                markeredgecolor='white', markeredgewidth=0.5, transform=ccrs.PlateCarree(), zorder=10)
            for spine in map_ax.spines.values():
                spine.set_edgecolor('#546E7A')
                spine.set_linewidth(1)
        except Exception as e:
            print(f"Warning: Map creation failed for {site} ({e}), continuing without map.")

    site_safe = site.replace(" ", "_").replace("(", "").replace(")", "")
    
    # Save files
    try:
        svg_filename = f"{site_safe}_diagram.svg"
        svg_path = os.path.join(output_folder, svg_filename)
        fig.savefig(svg_path, format='svg', bbox_inches='tight')
        print(f"   -> Saved SVG: {svg_path}")

        # Reduced DPI to 300 to prevent Memory Crash (OOM)
        png_filename = f"{site_safe}_diagram.png"
        png_path = os.path.join(output_folder, png_filename)
        fig.savefig(png_path, format='png', dpi=600, bbox_inches='tight')
        print(f"   -> Saved PNG: {png_path}")
    except Exception as e:
        print(f"   ❌ FAILED to save images for {site_safe}: {e}")

    # FORCE MEMORY CLEAR
    plt.clf()
    plt.close(fig)
    plt.close('all')
    gc.collect()

# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate soil depth / tower configuration diagrams for OzFlux sites.")
    parser.add_argument("--index", type=int, default=None, help="Index of the site to process (0-based) for Slurm array.")
    parser.add_argument("--force", action="store_true", help="Force regeneration of diagrams even if they already exist.")
    args = parser.parse_args()

    # Force non-interactive backend to save memory
    plt.switch_backend('Agg') 
    
    # Use absolute output directory to be safe during Slurm runs
    absolute_output_dir = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/FluxTower_Diagrams"

    print(f"Reading Data from: {INPUT_FILE}")
    try:
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not os.path.exists(absolute_output_dir):
        os.makedirs(absolute_output_dir)

    df['plot_depth'] = pd.to_numeric(df['plot_depth'], errors='coerce')
    df['plot_depth'] = -df['plot_depth'].abs()
    df = df.dropna(subset=['plot_depth'])

    grouped = df.groupby('Source File')
    # Sort groups by source file name so the indexing is deterministic
    sorted_groups = sorted(list(grouped), key=lambda x: str(x[0]))
    print(f"Found {len(sorted_groups)} unique sites to plot.\n")

    if args.index is not None:
        if args.index < 0 or args.index >= len(sorted_groups):
            print(f"❌ Index {args.index} is out of bounds (0 to {len(sorted_groups)-1})")
            return
        sorted_groups = [sorted_groups[args.index]]
        print(f"Processing single site at index {args.index}: {sorted_groups[0][0]}")

    for source_file, group in sorted_groups:
        clean_site_name = str(source_file).replace('_L6.nc', '').replace('.nc', '')
        site_folder = os.path.join(absolute_output_dir, clean_site_name)
        
        # --- RESUME LOGIC ---
        # Check if the PNG already exists. If so, skip this site (unless --force is passed).
        expected_png = os.path.join(site_folder, f"{clean_site_name.replace(' ','_')}_diagram.png")
        if os.path.exists(expected_png) and not args.force:
            print(f"⏩ Skipping {clean_site_name} (File exists)")
            continue
        
        if not os.path.exists(site_folder):
            os.makedirs(site_folder)

        first_row = group.iloc[0]
        t_start, t_end = str(first_row.get('Time Coverage Start', '')), str(first_row.get('Time Coverage End', ''))
        meta = {
            "site_name": clean_site_name,
            "fluxnet_id": first_row.get('FLUXNET ID'),
            "vegetation": first_row.get('Vegetation Type'),
            "latitude": first_row.get('Latitude'),
            "longitude": first_row.get('Longitude'),
            "altitude": first_row.get('Altitude_m'),
            "val_tower_h": first_row.get('Tower_Height_m', 15.0),
            "val_canopy_h": first_row.get('Canopy_Height_m', np.nan),
            "soil": first_row.get('Soil Type'),
            "period_str": f"{t_start[:4]}–{t_end[:4]}" if len(t_start)>=4 and len(t_end)>=4 else "?"
        }
        if pd.isna(meta['val_tower_h']): meta['val_tower_h'] = 15.0

        sensors = []
        for idx, row in group.iterrows():
            depth_m = row['plot_depth']
            label = format_sensor_label(row['Variable Name'], depth_m)
            sensors.append({"depth_m": depth_m, "plot_y": depth_m * 100.0, "label": label})

        sdata = pd.DataFrame(sensors).drop_duplicates(subset=['plot_y', 'label'])
        max_depth_cm = abs(sdata['plot_y'].min()) if not sdata.empty else 50.0
        
        # Scale Calculation
        needed_stack = (len(sdata) // 2) * LABEL_BUFFER
        visual_soil = max(max_depth_cm, needed_stack) + 10.0
        visual_soil = max(visual_soil, 50.0)
        
        if meta['val_tower_h'] > 0:
            plot_scale = max(2.0, min((visual_soil + 20) / meta['val_tower_h'], 12.0))
        else:
            plot_scale = 4.0

        print(f"📊 Processing Site: {clean_site_name} | Scale: {plot_scale:.2f}")
        
        try:
            render_plot(meta, sdata, -visual_soil, (meta['val_tower_h'] * plot_scale) + 70.0, plot_scale, site_folder)
        except Exception as e:
            print(f"❌ CRITICAL ERROR rendering {clean_site_name}: {e}")
            plt.close('all')

if __name__ == "__main__":
    main()