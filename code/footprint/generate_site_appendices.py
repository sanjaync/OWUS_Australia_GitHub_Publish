#!/usr/bin/env python3
"""
generate_site_appendices.py
===========================
Generates a separate LaTeX appendix report (.tex and compiled .pdf) for each site.
Downloads ESRI satellite imagery using Cartopy, overlays footprint contours,
adds a north arrow, dynamic scale bar, lat/lon gridline labels, and maps windroses.

Uses the 'ismn' environment containing Cartopy.

Output folder:
    output_L6new/<Site>/appendix/
        - appendix_<Site>.tex
        - appendix_<Site>.pdf
"""

import os, sys, re, zipfile, shutil, subprocess, argparse
import numpy as np
import xml.etree.ElementTree as ET
from configobj import ConfigObj
import netCDF4

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.io.img_tiles import GoogleWTS

OUTPUT_BASE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/PyFluxPro/OzFlux-footprint/output_L6new"
L6_DATA_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6"


# ── Esri Satellite Tile Provider ─────────────────────────────────────────────
class EsriSatellite(GoogleWTS):
    def _image_url(self, tile):
        x, y, z = tile
        return f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


# ── ESA WorldCover Tile Provider ─────────────────────────────────────────────
class EsaWorldCover(GoogleWTS):
    def _image_url(self, tile):
        x, y, z = tile
        # Level, Row, Col in WMTS is Z, Y, X
        # Using TileMatrixSet = EPSG:3857 (Web Mercator)
        return (
            "https://services.terrascope.be/wmts/v2"
            "?service=WMTS&request=GetTile&version=1.0.0"
            "&layer=WORLDCOVER_2021_MAP&style=default"
            "&format=image/png&tileMatrixSet=EPSG:3857"
            f"&tileMatrix=EPSG:3857:{z}&tileRow={y}&tileCol={x}"
        )


# ── Cartography Helpers ────────────────────────────────────────────────────────
def add_scale_bar(ax, length_m, location=(0.06, 0.08), color='white'):
    """Draws an accurate scale bar in meters on a Cartopy PlateCarree axis."""
    # Get current extent
    xmin, xmax, ymin, ymax = ax.get_extent(crs=ccrs.PlateCarree())
    lat_center = (ymin + ymax) / 2.0
    
    # Degrees longitude per meter = 1.0 / (111320.0 * cos(lat))
    m_per_deg_lon = 111320.0 * np.cos(np.radians(lat_center))
    deg_lon_length = length_m / m_per_deg_lon
    
    # Position in axes fraction coordinates
    ax_x, ax_y = location
    dx = xmax - xmin
    dy = ymax - ymin
    
    x_start = xmin + ax_x * dx
    y_start = ymin + ax_y * dy
    x_end = x_start + deg_lon_length
    
    # Shadow/contrast backing line
    ax.plot([x_start, x_end], [y_start, y_start], color='black', linewidth=4.5, transform=ccrs.PlateCarree(), zorder=19)
    # Scale bar line
    ax.plot([x_start, x_end], [y_start, y_start], color=color, linewidth=2.5, transform=ccrs.PlateCarree(), zorder=20)
    
    # Ticks
    tick_h = dy * 0.015
    ax.plot([x_start, x_start], [y_start - tick_h, y_start + tick_h], color='black', linewidth=2.5, transform=ccrs.PlateCarree(), zorder=19)
    ax.plot([x_start, x_start], [y_start - tick_h, y_start + tick_h], color=color, linewidth=1.5, transform=ccrs.PlateCarree(), zorder=20)
    ax.plot([x_end, x_end], [y_start - tick_h, y_start + tick_h], color='black', linewidth=2.5, transform=ccrs.PlateCarree(), zorder=19)
    ax.plot([x_end, x_end], [y_start - tick_h, y_start + tick_h], color=color, linewidth=1.5, transform=ccrs.PlateCarree(), zorder=20)
    
    # Label text (with black outline for contrast on satellite background)
    label_x = (x_start + x_end) / 2.0
    label_y = y_start + tick_h * 1.5
    
    txt = ax.text(label_x, label_y, f"{length_m} m", color=color, transform=ccrs.PlateCarree(),
                  weight='bold', ha='center', va='bottom', fontsize=9, zorder=22)
    # Add contrast path effects (black outline)
    import matplotlib.patheffects as path_effects
    txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='black')])


def add_north_arrow(ax, location=(0.94, 0.94)):
    """Draws a clean professional north arrow on the plot."""
    # Arrow line
    ax.annotate('N', xy=location, xytext=(location[0], location[1] - 0.07),
                arrowprops=dict(facecolor='white', edgecolor='black', width=1.5, headwidth=6, shrink=0.02),
                xycoords='axes fraction', textcoords='axes fraction',
                fontsize=11, weight='bold', color='white', ha='center', va='center', zorder=25)


# ── Metadata Parser ───────────────────────────────────────────────────────────
def parse_height(s):
    if not s or str(s).strip() in ('N/A', '', 'not defined'): return None
    s = re.sub(r'\s*m\b.*$', '', str(s).strip(), flags=re.IGNORECASE)
    s = re.sub(r'\(.*?\)', '', s).strip()
    m = re.match(r'([\d.]+)\s*[-–]\s*([\d.]+)', s)
    if m: return (float(m.group(1)) + float(m.group(2))) / 2.0
    try: return float(s)
    except ValueError: return None


def get_site_metadata(nc_path):
    try:
        nc = netCDF4.Dataset(nc_path, 'r')
        attrs = {a: getattr(nc, a) for a in nc.ncattrs()}
        nc.close()
    except Exception as e:
        print(f"Error reading NC file {nc_path}: {e}")
        attrs = {}
    
    th = parse_height(attrs.get('tower_height', attrs.get('measurement_height')))
    ch = parse_height(attrs.get('canopy_height', attrs.get('vegetation_height')))
    if th is None: th = 10.0
    if ch is None: ch = max(0.1, th * 0.1)
    
    return {
        'site_name':    attrs.get('site_name', os.path.basename(nc_path).replace('_L6.nc', '')),
        'tower_height': th,
        'canopy_height': ch,
        'latitude':  float(attrs.get('latitude', 0)),
        'longitude': float(attrs.get('longitude', 0)),
        'elevation': attrs.get('elevation', attrs.get('altitude', 'N/A')),
    }


# ── KML GroundOverlay Parser ──────────────────────────────────────────────────
def parse_kml_overlays(kml_path, mode='annual'):
    overlays = []
    if not os.path.exists(kml_path):
        return overlays
    
    tree = ET.parse(kml_path)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    for overlay in root.findall('.//kml:GroundOverlay', ns):
        icon = overlay.find('.//kml:Icon/kml:href', ns)
        href = icon.text if icon is not None else ""
        
        latlon = overlay.find('kml:LatLonBox', ns)
        if latlon is not None:
            north = float(latlon.find('kml:north', ns).text)
            south = float(latlon.find('kml:south', ns).text)
            east  = float(latlon.find('kml:east', ns).text)
            west  = float(latlon.find('kml:west', ns).text)
            
            # Extract date from href or filename
            # Example: Footprint_kljun200810010030.png
            m = re.search(r'\d{8}', href)
            if m:
                date_str = m.group(0) # "20081001"
                year = date_str[0:4]
                month = date_str[4:6]
                day = date_str[6:8]
                if mode == 'daily':
                    label = f"{year}-{month}-{day}"
                elif mode == 'monthly':
                    label = f"{year}-{month}"
                else: # annual
                    label = year
            else:
                m_yr = re.search(r'\d{4}', href)
                label = m_yr.group(0) if m_yr else "unknown"
            
            overlays.append({
                'href': href,
                'north': north,
                'south': south,
                'east': east,
                'west': west,
                'year': label  # Storing the formatted date label here
            })
    return overlays


# ── Cartographic Map Renderer ─────────────────────────────────────────────────
def render_cartographic_map(site_name, meta, overlay_info, app_dir, prefix, background='satellite'):
    """
    Renders the footprint PNG on top of ESRI satellite tiles or LULC tiles,
    complete with gridlines, north arrow, and dynamic scale bar.
    """
    img_name = overlay_info['href']
    raw_img_path = os.path.join(app_dir, img_name)
    if not os.path.exists(raw_img_path):
        return None
        
    try:
        img = plt.imread(raw_img_path)
    except Exception as e:
        print(f"Error reading image {raw_img_path}: {e}")
        return None

    w = overlay_info['west']
    e = overlay_info['east']
    s = overlay_info['south']
    n = overlay_info['north']

    if background == 'lulc':
        tiler = EsaWorldCover()
        zoom = 14
    else:
        tiler = EsriSatellite()
        zoom = 17
    
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1, projection=tiler.crs)
    
    # 20% Padding to display footprint boundary context
    pad_x = (e - w) * 0.20
    pad_y = (n - s) * 0.20
    ax.set_extent([w - pad_x, e + pad_x, s - pad_y, n + pad_y], crs=ccrs.PlateCarree())
    
    # Add imagery tiles
    try:
        ax.add_image(tiler, zoom)
    except Exception:
        # Fallback to lower zoom level if it fails
        try:
            ax.add_image(tiler, zoom - 1)
        except Exception as tile_err:
            print(f"Warning: Failed to fetch background tiles: {tile_err}")
            
    # Overlay transparent footprint PNG
    ax.imshow(img, extent=[w, e, s, n], transform=ccrs.PlateCarree(), origin='upper', zorder=5)
    
    # Define custom A-frame Flux Tower Marker Path
    from matplotlib.path import Path
    verts = [
        (-0.4, -0.8), # bottom left
        (0.0, 0.8),   # top center
        (0.4, -0.8),  # bottom right
        (-0.2, -0.1), # crossbar left
        (0.2, -0.1),  # crossbar right
        (0.0, 0.8),   # top center
        (0.0, 1.2),   # antenna tip
    ]
    codes = [
        Path.MOVETO,
        Path.LINETO,
        Path.LINETO,
        Path.MOVETO,
        Path.LINETO,
        Path.MOVETO,
        Path.LINETO,
    ]
    tower_marker = Path(verts, codes)

    # Mark Tower Location with the custom tower icon
    ax.plot(meta['longitude'], meta['latitude'], marker=tower_marker, color='red', 
            markeredgecolor='black', markeredgewidth=0.8, markersize=14, 
            label='Flux Tower', transform=ccrs.PlateCarree(), zorder=10)
            
    # Professional Grid lines and coordinate labels
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, 
                      color='white', linestyle='--', linewidth=0.5, zorder=8)
    gl.top_labels = False
    gl.right_labels = False
    gl.xlabel_style = {'size': 8}
    gl.ylabel_style = {'size': 8}
    
    # Dynamic Scale Bar Calculation
    # Approximate width in meters
    width_m = (e - w) * 111320.0 * np.cos(np.radians(meta['latitude']))
    if width_m < 350:
        scale_len = 50
    elif width_m < 700:
        scale_len = 100
    elif width_m < 1500:
        scale_len = 200
    else:
        scale_len = 500
        
    # Embed Colorbar Legend as an Inset inside the map (Prevent stretching)
    cbar_path = os.path.join(app_dir, 'cbar.png')
    if os.path.exists(cbar_path):
        try:
            cbar_img = plt.imread(cbar_path)
            cbar_ax = ax.inset_axes([0.90, 0.20, 0.08, 0.6])
            cbar_ax.imshow(cbar_img, aspect='equal')
            cbar_ax.axis('off')
            
            # Label above colorbar
            import matplotlib.patheffects as path_effects
            ax.text(0.94, 0.82, '(%)', transform=ax.transAxes, color='white', 
                    weight='bold', ha='center', va='bottom', fontsize=8, zorder=25,
                    path_effects=[path_effects.withStroke(linewidth=2, foreground='black')])
        except Exception as cbar_err:
            print(f"Warning: Failed to add inset colorbar: {cbar_err}")

    add_scale_bar(ax, scale_len, color='white')
    add_north_arrow(ax)
    
    plt.legend(loc='lower right', framealpha=0.8, fontsize=8).set_zorder(30)
    
    output_filename = f"{prefix}_map_{overlay_info['year']}.jpg"
    output_path = os.path.join(app_dir, output_filename)
    plt.savefig(output_path, dpi=180, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    return output_filename


# ── LaTeX Appendix Generator ──────────────────────────────────────────────────
def generate_latex(site_name, meta, kormei_maps, kljun_maps, windrose_jpgs, app_dir, cbar_img, mode='annual', background='satellite'):
    tex_filename = f"appendix_{site_name}_{mode}.tex" if background == 'satellite' else f"appendix_{site_name}_{mode}_{background}.tex"
    tex_path = os.path.join(app_dir, tex_filename)
    
    # Find all available years/periods
    all_years = sorted(list(set(kormei_maps.keys()) | set(kljun_maps.keys()) | set(windrose_jpgs.keys())))

    with open(tex_path, 'w') as f:
        f.write(r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.55in]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage{caption}
\usepackage{subcaption}
\usepackage{microtype}
\usepackage{xcolor}
\usepackage{hyperref}

\pagestyle{fancy}
\fancyhf{}
\rhead{\textcolor{gray}{""" + site_name + r""" Appendix}}
\lhead{\textcolor{gray}{OzFlux Footprint Report}}
\cfoot{\thepage}

\begin{document}

\title{\textbf{Appendix: Site Footprint and Climatology Analysis \\ (Mode: """ + mode.capitalize() + r""") \\ """ + site_name + r"""}}
\author{\textbf{OzFlux Footprint Processing Pipeline}}
\date{\today}
\maketitle

\section{Site Metadata Summary}
The table below summarizes the key attributes and configuration of the flux tower station.

\begin{table}[H]
\centering
\begin{tabular}{ll}
\toprule
\textbf{Attribute} & \textbf{Value} \\
\midrule
Station Name & """ + meta['site_name'] + r""" \\
Latitude & """ + f"{meta['latitude']:.5f}" + r"""~$^{\circ}$S \\
Longitude & """ + f"{meta['longitude']:.5f}" + r"""~$^{\circ}$E \\
Elevation / Altitude & """ + str(meta['elevation']) + r""" \\
Measurement Height (Tower) & """ + f"{meta['tower_height']:.1f}" + r"""~m \\
Canopy Height (Vegetation) & """ + f"{meta['canopy_height']:.1f}" + r"""~m \\
\bottomrule
\end{tabular}
\caption{Flux station metadata parameters extracted from L6 netCDF dataset.}
\label{tab:metadata}
\end{table}

\newpage
\section{""" + mode.capitalize() + r""" Footprint and Climatology Comparison}
For each """ + mode + r""" period of available data, this section presents:
\begin{enumerate}
    \item \textbf{Kormann-Meixner Footprint Map}: High-resolution satellite view overlaid with footprint contours, including a scale bar, lat/lon coordinate grid, and north arrow.
    \item \textbf{Kljun Footprint Map}: High-resolution satellite view overlaid with Kljun parameterization model footprint contours.
    \item \textbf{Wind Rose}: Frequency distribution of wind speed and wind direction sectors.
\end{enumerate}

""")

        for yr in all_years:
            kormei_map = kormei_maps.get(yr)
            kljun_map = kljun_maps.get(yr)
            wr_img = windrose_jpgs.get(yr)
            
            if not (kormei_map or kljun_map or wr_img):
                continue
                
            f.write(r"\subsection{" + mode.capitalize() + r" Period: " + yr + r"}" + "\n")
            
            # Row 1: Side-by-side Footprints
            f.write(r"\begin{figure}[H]" + "\n")
            f.write(r"  \centering" + "\n")
            
            if kormei_map:
                f.write(r"  \begin{subfigure}[b]{0.48\textwidth}" + "\n")
                f.write(r"    \centering" + "\n")
                f.write(r"    \includegraphics[width=\textwidth]{" + kormei_map + r"}" + "\n")
                f.write(r"    \caption{Kormann-Meixner Map}" + "\n")
                f.write(r"  \end{subfigure}" + "\n")
                f.write(r"  \hfill" + "\n")
                
            if kljun_map:
                f.write(r"  \begin{subfigure}[b]{0.48\textwidth}" + "\n")
                f.write(r"    \centering" + "\n")
                f.write(r"    \includegraphics[width=\textwidth]{" + kljun_map + r"}" + "\n")
                f.write(r"    \caption{Kljun Map}" + "\n")
                f.write(r"  \end{subfigure}" + "\n")
                
            bg_label = "LULC" if background == "lulc" else "satellite"
            f.write(r"  \caption{" + mode.capitalize() + r" footprint " + bg_label + r" mapping comparisons for " + site_name + " in " + yr + ".}" + "\n")
            f.write(r"  \label{fig:footprints_" + yr + "}" + "\n")
            f.write(r"\end{figure}" + "\n\n")
            
            # Row 2: Wind Rose
            if wr_img:
                f.write(r"\begin{figure}[H]" + "\n")
                f.write(r"  \centering" + "\n")
                f.write(r"  \includegraphics[width=0.55\textwidth]{" + wr_img + r"}" + "\n")
                f.write(r"  \caption{" + mode.capitalize() + r" wind rose showing frequency distribution of wind speed and direction sectors for " + site_name + " in " + yr + ".}" + "\n")
                f.write(r"  \label{fig:windrose_" + yr + "}" + "\n")
                f.write(r"\end{figure}" + "\n\n")
                
            f.write(r"\newpage" + "\n")

        f.write(r"\end{document}" + "\n")
    return tex_path


def compile_latex(tex_path, app_dir):
    try:
        cmd = ["pdflatex", "-interaction=nonstopmode", os.path.basename(tex_path)]
        subprocess.run(cmd, cwd=app_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(cmd, cwd=app_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pdf_name = os.path.basename(tex_path).replace('.tex', '.pdf')
        pdf_path = os.path.join(app_dir, pdf_name)
        if os.path.exists(pdf_path):
            return pdf_path
    except Exception as e:
        print(f"Compilation failed for {tex_path}: {e}")
    return None


def cleanup_temp_files(app_dir, site_name, mode, background='satellite'):
    # Remove only LaTeX compilation logs/temp files and raw transparent footprint PNGs.
    # Keep final map JPGs, windrose JPGs, cbar.png and PDFs.
    tex_filename = f"appendix_{site_name}_{mode}.tex" if background == 'satellite' else f"appendix_{site_name}_{mode}_{background}.tex"
    for f in os.listdir(app_dir):
        # Keep list
        if f.endswith('.pdf'):
            continue
        if 'map_' in f and f.endswith('.jpg'):
            continue
        if 'windrose_' in f and f.endswith('.jpg'):
            continue
        if f == 'cbar.png':
            continue
            
        # Delete list
        if f.endswith(('.aux', '.log', '.out', '.kml', '.png')) or f == tex_filename:
            try:
                os.remove(os.path.join(app_dir, f))
            except Exception:
                pass


def process_site(site_name, mode='annual', background='satellite'):
    print(f"\nProcessing Appendix for: {site_name} (Mode: {mode}, Background: {background})")
    
    site_dir = os.path.join(OUTPUT_BASE, site_name)
    if mode == 'annual':
        app_folder = 'appendix' if background == 'satellite' else f'appendix_{background}'
    else:
        app_folder = f'appendix_{mode}' if background == 'satellite' else f'appendix_{mode}_{background}'
        
    app_dir  = os.path.join(site_dir, app_folder)
    os.makedirs(app_dir, exist_ok=True)
    
    # 1. Get site metadata
    nc_path = os.path.join(L6_DATA_DIR, f"{site_name}_L6.nc")
    if not os.path.exists(nc_path):
        nc_files = [f for f in os.listdir(L6_DATA_DIR) if f.startswith(site_name) and f.endswith('_L6.nc')]
        if nc_files:
            nc_path = os.path.join(L6_DATA_DIR, nc_files[0])
        else:
            print(f"  Missing NC file for {site_name} in {L6_DATA_DIR}")
            return False

    meta = get_site_metadata(nc_path)
    
    # 2. Extract and parse Kormann-Meixner KMZ
    kormei_kmz = os.path.join(site_dir, 'plots', f'kormei_{mode}', f"{site_name}_kormei_fp.kmz")
    if not os.path.exists(kormei_kmz) and os.path.isdir(os.path.join(site_dir, 'plots', f'kormei_{mode}')):
        kmzs = [f for f in os.listdir(os.path.join(site_dir, 'plots', f'kormei_{mode}')) if f.endswith('.kmz')]
        if kmzs: kormei_kmz = os.path.join(site_dir, 'plots', f'kormei_{mode}', kmzs[0])

    kormei_maps = {}
    cbar_filename = None
    if os.path.exists(kormei_kmz):
        with zipfile.ZipFile(kormei_kmz, 'r') as zf:
            zf.extractall(app_dir)
        kml_files = [f for f in os.listdir(app_dir) if f.endswith('.kml')]
        if kml_files:
            kml_path = os.path.join(app_dir, kml_files[0])
            overlays = parse_kml_overlays(kml_path, mode)
            for ov in overlays:
                map_jpg = render_cartographic_map(site_name, meta, ov, app_dir, 'kormei', background)
                if map_jpg:
                    kormei_maps[ov['year']] = map_jpg
            # Clean up extracted kml
            os.remove(kml_path)
            
        # Get colorbar legend
        if os.path.exists(os.path.join(app_dir, 'cbar.png')):
            cbar_filename = 'cbar.png'
            
    # 3. Extract and parse Kljun KMZ
    kljun_kmz = os.path.join(site_dir, 'plots', f'kljun_{mode}', f"{site_name}_kljun_fp.kmz")
    if not os.path.exists(kljun_kmz) and os.path.isdir(os.path.join(site_dir, 'plots', f'kljun_{mode}')):
        kmzs = [f for f in os.listdir(os.path.join(site_dir, 'plots', f'kljun_{mode}')) if f.endswith('.kmz')]
        if kmzs: kljun_kmz = os.path.join(site_dir, 'plots', f'kljun_{mode}', kmzs[0])

    kljun_maps = {}
    if os.path.exists(kljun_kmz):
        with zipfile.ZipFile(kljun_kmz, 'r') as zf:
            zf.extractall(app_dir)
        kml_files = [f for f in os.listdir(app_dir) if f.endswith('.kml')]
        if kml_files:
            kml_path = os.path.join(app_dir, kml_files[0])
            overlays = parse_kml_overlays(kml_path, mode)
            for ov in overlays:
                map_jpg = render_cartographic_map(site_name, meta, ov, app_dir, 'kljun', background)
                if map_jpg:
                    kljun_maps[ov['year']] = map_jpg
            os.remove(kml_path)
            
        if not cbar_filename and os.path.exists(os.path.join(app_dir, 'cbar.png')):
            cbar_filename = 'cbar.png'

    # 4. Map Windrose JPG files
    wr_dir = os.path.join(site_dir, 'plots', f'windrose_{mode}')
    windrose_jpgs = {}
    if os.path.isdir(wr_dir):
        wr_files = sorted([f for f in os.listdir(wr_dir) if f.endswith('.jpg') and f.startswith('Windrose_')])
        fp_periods = sorted(list(set(kormei_maps.keys()) | set(kljun_maps.keys())))
        
        for idx, prd in enumerate(fp_periods):
            if idx < len(wr_files):
                src_wr = os.path.join(wr_dir, wr_files[idx])
                dst_name = f"windrose_{prd}.jpg"
                shutil.copy2(src_wr, os.path.join(app_dir, dst_name))
                windrose_jpgs[prd] = dst_name

    if not kormei_maps and not kljun_maps:
        print(f"  No footprint overlays could be rendered for {site_name} in {mode} mode")
        cleanup_temp_files(app_dir, site_name, mode, background)
        return False
        
    # 5. Generate LaTeX
    tex_path = generate_latex(site_name, meta, kormei_maps, kljun_maps, windrose_jpgs, app_dir, cbar_filename, mode, background)
    
    # 6. Compile to PDF
    pdf_path = compile_latex(tex_path, app_dir)
    
    # 7. Clean up intermediate files
    cleanup_temp_files(app_dir, site_name, mode, background)
    
    if pdf_path:
        print(f"  SUCCESS: Created {pdf_path}")
        return True
    else:
        print(f"  FAILED to compile PDF for {site_name}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX and PDF site appendix reports.")
    parser.add_argument('--site', type=str, help='Process one site only')
    parser.add_argument('--mode', type=str, choices=['annual', 'monthly', 'daily'], default='annual',
                        help='Footprint climatology mode (annual, monthly, daily)')
    parser.add_argument('--background', type=str, choices=['satellite', 'lulc'], default='satellite',
                        help='Background map imagery style (satellite, lulc)')
    args = parser.parse_args()
    
    if not os.path.isdir(OUTPUT_BASE):
        print(f"Output directory not found: {OUTPUT_BASE}")
        sys.exit(1)
        
    sites = sorted(os.listdir(OUTPUT_BASE))
    if args.site:
        sites = [s for s in sites if s == args.site]
        if not sites:
            print(f"Site '{args.site}' not found in {OUTPUT_BASE}")
            sys.exit(1)
            
    success_count = 0
    total_count = 0
    for site in sites:
        if os.path.isdir(os.path.join(OUTPUT_BASE, site, 'plots')):
            total_count += 1
            if process_site(site, args.mode, args.background):
                success_count += 1
                
    print(f"\n==========================================")
    print(f"Appendices generated: {success_count} / {total_count} (Mode: {args.mode}, Background: {args.background})")
    print(f"==========================================")


if __name__ == '__main__':
    main()
