#!/usr/bin/env python3
"""
convert_kmz_for_ge_online.py
============================
Standalone post-processor — does NOT modify any original scripts, KMZ files or folders.

For each site, reads existing KMZ files from their original folders and writes
new GE Online compatible versions into:

    output/<Site>/ge_online/<Site>_<model>_<climatology>_ge_online.kmz

Changes made to KML inside each new KMZ:
  - <ScreenOverlay> removed  (not supported by Google Earth Online)
  - <TimeSpan> removed       (not supported by Google Earth Online)

ALL original files and folders are left completely untouched.

Submit on compute node:
    sbatch submit_ge_online_convert.sh

Or run directly:
    python3 convert_kmz_for_ge_online.py
    python3 convert_kmz_for_ge_online.py --site Calperum
"""

import os, sys, re, zipfile, argparse

OUTPUT = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/PyFluxPro/OzFlux-footprint/output"

# Maps subfolder name → (model, climatology) for output filename
FOLDER_MAP = {
    'kormei_daily':   ('kormei', 'daily'),
    'kormei_monthly': ('kormei', 'monthly'),
    'kormei_annual':  ('kormei', 'annual'),
    'kljun_daily':    ('kljun',  'daily'),
    'kljun_monthly':  ('kljun',  'monthly'),
    'kljun_annual':   ('kljun',  'annual'),
}


def strip_kml_for_ge_online(kml_text):
    """Remove <ScreenOverlay> and <TimeSpan> blocks — not supported by GE Online."""
    kml_text = re.sub(r'\s*<ScreenOverlay>.*?</ScreenOverlay>', '',
                      kml_text, flags=re.DOTALL)
    kml_text = re.sub(r'\s*<TimeSpan>.*?</TimeSpan>', '',
                      kml_text, flags=re.DOTALL)
    return kml_text


def convert_site(site_name):
    site_plots  = os.path.join(OUTPUT, site_name, 'plots')
    ge_out_dir  = os.path.join(OUTPUT, site_name, 'ge_online')

    if not os.path.isdir(site_plots):
        return 0, 0

    os.makedirs(ge_out_dir, exist_ok=True)

    converted = 0
    skipped   = 0

    for folder_name, (model, clim) in FOLDER_MAP.items():
        src_folder = os.path.join(site_plots, folder_name)
        if not os.path.isdir(src_folder):
            skipped += 1
            continue

        # Find the original KMZ in this folder (ignore any _ge_online ones)
        kmzs = [f for f in os.listdir(src_folder)
                if f.endswith('.kmz') and '_ge_online' not in f]
        if not kmzs:
            skipped += 1
            continue

        src_kmz = os.path.join(src_folder, kmzs[0])
        # New name includes model and climatology so all 6 per site are distinct
        out_name = f"{site_name}_{model}_{clim}_ge_online.kmz"
        out_path = os.path.join(ge_out_dir, out_name)

        try:
            with zipfile.ZipFile(src_kmz, 'r') as src_zf:
                names = src_zf.namelist()
                kmls  = [n for n in names if n.endswith('.kml')]
                if not kmls:
                    skipped += 1
                    continue

                with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED) as dst_zf:
                    for name in names:
                        data = src_zf.read(name)
                        if name in kmls:
                            kml_text = strip_kml_for_ge_online(data.decode('utf-8'))
                            dst_zf.writestr(name, kml_text.encode('utf-8'))
                        else:
                            dst_zf.writestr(name, data)   # PNGs copied unchanged

            orig_kb = os.path.getsize(src_kmz) / 1024
            new_kb  = os.path.getsize(out_path)  / 1024
            print(f"    OK  {out_name}  ({orig_kb:.0f} KB → {new_kb:.0f} KB)")
            converted += 1

        except Exception as e:
            print(f"    FAIL {out_name}: {e}")
            skipped += 1

    return converted, skipped


def main():
    parser = argparse.ArgumentParser(
        description='Convert OzFlux footprint KMZs to Google Earth Online compatible format')
    parser.add_argument('--site', type=str, help='Convert one site only (e.g. Calperum)')
    parser.add_argument('--output-dir', type=str, default=None, help='Override output base directory')
    args = parser.parse_args()

    global OUTPUT
    if args.output_dir:
        OUTPUT = args.output_dir

    if not os.path.isdir(OUTPUT):
        print(f"ERROR: Output directory not found: {OUTPUT}")
        sys.exit(1)

    all_sites = sorted(os.listdir(OUTPUT))
    if args.site:
        all_sites = [s for s in all_sites if s == args.site]
        if not all_sites:
            print(f"ERROR: Site '{args.site}' not found in {OUTPUT}")
            sys.exit(1)

    total_ok   = 0
    total_skip = 0

    for site in all_sites:
        print(f"\n{site}")
        ok, skip = convert_site(site)
        total_ok   += ok
        total_skip += skip

    print(f"\n{'='*60}")
    print(f"Converted: {total_ok}  |  Skipped/missing: {total_skip}")
    print(f"\nGE Online KMZs saved in:")
    print(f"  output/<Site>/ge_online/<Site>_<model>_<clim>_ge_online.kmz")
    print(f"\nOriginal files and folders: UNCHANGED")


if __name__ == '__main__':
    main()
