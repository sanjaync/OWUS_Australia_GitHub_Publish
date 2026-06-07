#!/usr/bin/env python3
"""
OzFlux Footprint Analysis — Full Batch Runner
Runs ALL 9 analyses per site:

  Footprint models (× 3 climatologies):
    1.  kormei / Daily    → output/<Site>/plots/kormei_daily/
    2.  kormei / Monthly  → output/<Site>/plots/kormei_monthly/
    3.  kormei / Annual   → output/<Site>/plots/kormei_annual/
    4.  kljun  / Daily    → output/<Site>/plots/kljun_daily/
    5.  kljun  / Monthly  → output/<Site>/plots/kljun_monthly/
    6.  kljun  / Annual   → output/<Site>/plots/kljun_annual/

  Windrose (× 3 climatologies):
    7.  windrose / Daily    → output/<Site>/plots/windrose_daily/
    8.  windrose / Monthly  → output/<Site>/plots/windrose_monthly/
    9.  windrose / Annual   → output/<Site>/plots/windrose_annual/

  Each footprint folder contains:
    <Site>_<model>_fp.kmz   ← Google Earth KMZ with PNG overlays
    Footprint_<model><ts>.jpg ← standalone JPG per period

  Each windrose folder contains:
    Windrose_<Site><index>.jpg ← windrose plot per period

  NetCDF output:  output/<Site>/results/<Site>_<d|m|y>_fp.nc

Usage:
    python run_all_footprints.py                    # all sites
    python run_all_footprints.py --site Calperum    # single site
    python run_all_footprints.py --index 0          # SLURM array index
    python run_all_footprints.py --list             # list sites
"""

import os
import sys
import re
import argparse
import logging
import datetime
import time
import traceback

# ── Python 2→3 compat patches ───────────────────────────────────────────────
import builtins
builtins.unicode = str

import types
for _m in ['Tkinter', 'tkFileDialog', 'tkMessageBox', 'tkSimpleDialog']:
    sys.modules[_m] = types.ModuleType(_m)

import matplotlib
matplotlib.use('Agg')

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')
sys.path.insert(0, SCRIPT_DIR)

from configobj import ConfigObj
import netCDF4
import numpy

# ── Configuration ────────────────────────────────────────────────────────────
L6_DATA_DIR = '/home/sanjays/et97_scratch2/oldscratch/Ozflux_L6'
FP_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.join(FP_BASE_DIR, 'output')
CF_DIR      = os.path.join(FP_BASE_DIR, 'controlfiles')

IPLOT      = 2    # 1=JPG only, 2=KMZ+PNG+JPG
NUM_CELLS  = 200  # grid cells per side (footprint_size/num_cells = cell width m)

CLIMATOLOGIES = ['Daily', 'Monthly', 'Annual']

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_height(s):
    if not s or str(s).strip() in ('N/A', '', 'not defined'): return None
    s = re.sub(r'\s*m\b.*$', '', str(s).strip(), flags=re.IGNORECASE)
    s = re.sub(r'\(.*?\)', '', s).strip()
    m = re.match(r'([\d.]+)\s*[-–]\s*([\d.]+)', s)
    if m: return (float(m.group(1)) + float(m.group(2))) / 2.0
    try: return float(s)
    except ValueError: return None


def get_site_metadata(nc_path):
    nc = netCDF4.Dataset(nc_path, 'r')
    attrs = {a: getattr(nc, a) for a in nc.ncattrs()}
    nc.close()
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
    }


def fp_size(th, ch):
    zm_d = th - (2.0/3.0 * ch)
    if   zm_d <  5: return 300
    elif zm_d < 15: return 500
    elif zm_d < 30: return 1000
    else:           return 2000


def make_symlink(nc_path, results_dir):
    fname = os.path.basename(nc_path)
    dest  = os.path.join(results_dir, fname)
    if not os.path.exists(dest):
        try: os.symlink(nc_path, dest)
        except FileExistsError: pass
    return fname

# ── Control file builders ─────────────────────────────────────────────────────
def footprint_cf(site_name, nc_path, meta, model, clim):
    """Build ConfigObj for one footprint run."""
    results_dir = os.path.join(OUTPUT_BASE, site_name, 'results')
    plots_dir   = os.path.join(OUTPUT_BASE, site_name, 'plots', f'{model}_{clim.lower()}')
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(plots_dir,   exist_ok=True)

    fname = make_symlink(nc_path, results_dir)

    cf = ConfigObj()
    cf.filename = os.path.join(CF_DIR, f'fp_{site_name}_{model}_{clim.lower()}.txt')
    cf['Files'] = {
        'file_path':   results_dir + '/',
        'in_filename': fname,
        'plot_path':   plots_dir  + '/',
    }
    cf['Tower'] = {
        'tower_height':   str(meta['tower_height']),
        'canopy_height':  str(meta['canopy_height']),
        'footprint_size': str(fp_size(meta['tower_height'], meta['canopy_height'])),
        'num_cells':      str(NUM_CELLS),
    }
    cf['Options'] = {'Climatology': clim, 'Cumulative': 'Yes', 'call_mode': 'batch'}
    cf['General'] = {'iplot': str(IPLOT), 'PlotWidth': '5.0', 'PlotHeight': '5.0',
                     'OzFlux_area_image': 'None'}
    cf.write()
    return cf


def windrose_cf(site_name, nc_path, meta, clim):
    """Build ConfigObj for one windrose run."""
    results_dir = os.path.join(OUTPUT_BASE, site_name, 'results')
    plots_dir   = os.path.join(OUTPUT_BASE, site_name, 'plots', f'windrose_{clim.lower()}')
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(plots_dir,   exist_ok=True)

    fname = make_symlink(nc_path, results_dir)

    cf = ConfigObj()
    cf.filename = os.path.join(CF_DIR, f'fp_{site_name}_windrose_{clim.lower()}.txt')
    cf['Files'] = {
        'file_path':   results_dir + '/',
        'in_filename': fname,
        'plot_path':   plots_dir  + '/',
    }
    cf['Options'] = {'Climatology': clim, 'call_mode': 'batch'}
    cf['General'] = {'PlotWidth': '10.0', 'PlotHeight': '10.0'}
    cf.write()
    return cf

# ── Runners ───────────────────────────────────────────────────────────────────
def run_footprint(site_name, nc_path, model, clim, logger):
    meta = get_site_metadata(nc_path)
    cf   = footprint_cf(site_name, nc_path, meta, model, clim)
    cf['controlfile_name'] = cf.filename
    cf['Options']['call_mode'] = 'batch'

    import footprint_fp
    t0 = time.time()
    footprint_fp.footprint_main(cf, model)
    logger.info(f'    {model}/{clim} completed in {time.time()-t0:.1f}s')
    return True


def run_windrose(site_name, nc_path, clim, logger):
    meta = get_site_metadata(nc_path)
    cf   = windrose_cf(site_name, nc_path, meta, clim)
    cf['controlfile_name'] = cf.filename
    cf['Options']['call_mode'] = 'batch'

    import footprint_wr
    t0 = time.time()
    footprint_wr.windrose_main(cf)
    logger.info(f'    windrose/{clim} completed in {time.time()-t0:.1f}s')
    return True

# ── Per-site orchestration ────────────────────────────────────────────────────
def run_all_for_site(site_name, nc_path, logger, windrose_only=False):
    logger.info('=' * 70)
    logger.info(f'  Site: {site_name}')
    logger.info('=' * 70)

    meta = get_site_metadata(nc_path)
    logger.info(f'  Tower: {meta["tower_height"]}m  Canopy: {meta["canopy_height"]}m  '
                f'Lat/Lon: ({meta["latitude"]}, {meta["longitude"]})')

    # Build task list
    tasks = []
    if not windrose_only:
        for clim in CLIMATOLOGIES:
            tasks.append(('footprint', 'kormei', clim))
            tasks.append(('footprint', 'kljun',  clim))
    for clim in CLIMATOLOGIES:
        tasks.append(('windrose', None, clim))

    results = {}
    for step, (kind, model, clim) in enumerate(tasks, 1):
        tag = f'{model}/{clim}' if model else f'windrose/{clim}'
        logger.info(f'  [{step}/{len(tasks)}] Running {tag}...')
        try:
            if kind == 'footprint':
                results[tag] = run_footprint(site_name, nc_path, model, clim, logger)
            else:
                results[tag] = run_windrose(site_name, nc_path, clim, logger)
        except Exception as e:
            logger.error(f'    FAILED {tag}: {e}')
            logger.error(traceback.format_exc())
            results[tag] = False

    return results

# ── Site discovery ─────────────────────────────────────────────────────────────
def get_all_sites():
    files = sorted(f for f in os.listdir(L6_DATA_DIR) if f.endswith('_L6.nc'))
    return [(f.replace('_L6.nc', ''), os.path.join(L6_DATA_DIR, f)) for f in files]

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site',          type=str)
    parser.add_argument('--index',         type=int)
    parser.add_argument('--list',          action='store_true')
    parser.add_argument('--windrose-only', action='store_true', help='Run only windrose')
    parser.add_argument('--data-dir',      type=str, default=None, help='Override L6 data directory')
    parser.add_argument('--output-dir',    type=str, default=None, help='Override output base directory')
    args = parser.parse_args()

    # Apply directory overrides (leave defaults if not supplied)
    global L6_DATA_DIR, OUTPUT_BASE, CF_DIR
    if args.data_dir:   L6_DATA_DIR = args.data_dir
    if args.output_dir: OUTPUT_BASE = args.output_dir
    CF_DIR = os.path.join(OUTPUT_BASE, 'controlfiles')

    os.makedirs(os.path.join(FP_BASE_DIR, 'logfiles'), exist_ok=True)
    os.makedirs(OUTPUT_BASE, exist_ok=True)
    os.makedirs(CF_DIR,      exist_ok=True)

    ts      = datetime.datetime.now().strftime('%Y%m%d%H%M')
    idx_str = f'_idx{args.index}' if args.index is not None else ''
    log_path = os.path.join(FP_BASE_DIR, 'logfiles', f'footprint_batch_{ts}{idx_str}.log')

    logger = logging.getLogger('footprint_log')
    logger.setLevel(logging.DEBUG)
    for h in logger.handlers[:]: logger.removeHandler(h)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh  = logging.FileHandler(log_path); fh.setFormatter(fmt)
    ch  = logging.StreamHandler();       ch.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(ch)

    all_sites = get_all_sites()

    if args.list:
        print(f'\nAvailable sites ({len(all_sites)}):')
        for i, (name, path) in enumerate(all_sites):
            m = get_site_metadata(path)
            print(f'  [{i:2d}] {name:45s} tower={m["tower_height"]:.1f}m')
        return

    if args.site:
        sites = [(n, p) for n, p in all_sites if n == args.site]
        if not sites:
            print(f"Error: site '{args.site}' not found. Use --list.")
            sys.exit(1)
    elif args.index is not None:
        if 0 <= args.index < len(all_sites):
            sites = [all_sites[args.index]]
        else:
            print(f'Error: index {args.index} out of range (0-{len(all_sites)-1})')
            sys.exit(1)
    else:
        sites = all_sites

    wo = args.windrose_only
    mode_str = 'windrose ONLY' if wo else '9 analyses each (kormei+kljun × Daily/Monthly/Annual + windrose × Daily/Monthly/Annual)'
    logger.info(f'OzFlux Footprint — {len(sites)} site(s) | {mode_str}')
    logger.info(f'Grid: {NUM_CELLS}×{NUM_CELLS} | iplot={IPLOT}')

    all_results = {}
    for site_name, nc_path in sites:
        all_results[site_name] = run_all_for_site(site_name, nc_path, logger, windrose_only=wo)

    logger.info('')
    logger.info('=' * 70)
    logger.info(' FINAL SUMMARY')
    logger.info('=' * 70)
    for site, res in all_results.items():
        ok   = sum(1 for v in res.values() if v)
        fail = [k for k, v in res.items() if not v]
        status = f'OK={ok}/{len(res)}'
        if fail: status += f'  FAIL={fail}'
        logger.info(f'  {site:45s} {status}')
    logger.info(f'  Output: {OUTPUT_BASE}')


if __name__ == '__main__':
    main()
