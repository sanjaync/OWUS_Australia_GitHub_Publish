import os
import xarray as xr
import glob

# Constants
METADATA_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6"
DIAGRAM_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/FluxTower_Diagrams"
OUTPUT_MD = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/OzFlux_Tower_Report.md"
OUTPUT_PDF = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/OzFlux_Tower_Report.pdf"

def clean_site_name(name):
    """Remove spaces and special characters for matching folder names."""
    return name.replace(" ", "").replace("-", "").replace("_", "")

def get_metadata(nc_file):
    """Extract global attributes from a NetCDF file."""
    try:
        with xr.open_dataset(nc_file) as ds:
            attrs = ds.attrs
            return {
                "site_name": attrs.get("site_name", "N/A"),
                "latitude": attrs.get("latitude", "N/A"),
                "longitude": attrs.get("longitude", "N/A"),
                "site_pi": attrs.get("site_pi", "N/A"),
                "soil": attrs.get("soil", "N/A"),
                "institution": attrs.get("institution", "N/A"),
                "data_link": attrs.get("data_link", "N/A"),
                "elevation": attrs.get("elevation", "N/A"),
                "vegetation": attrs.get("vegetation", "N/A"),
                "coverage": attrs.get("time_coverage_start", "N/A") + " to " + attrs.get("time_coverage_end", "N/A")
            }
    except Exception as e:
        print(f"Error reading {nc_file}: {e}")
        return None

def main():
    nc_files = glob.glob(os.path.join(METADATA_DIR, "*_L6_Summary.nc"))
    sites = []

    for nc in nc_files:
        meta = get_metadata(nc)
        if meta:
            # Match with diagram
            site_key = clean_site_name(meta["site_name"])
            # The diagram folders names are listed in the DIAGRAM_DIR
            diagram_folder = None
            for folder in os.listdir(DIAGRAM_DIR):
                if clean_site_name(folder).lower() == site_key.lower():
                    diagram_folder = folder
                    break
            
            if diagram_folder:
                diagram_path = os.path.join(DIAGRAM_DIR, diagram_folder, f"{diagram_folder}_diagram.png")
                if os.path.exists(diagram_path):
                    meta["diagram"] = diagram_path
                else:
                    # Try alternative diagram names
                    pngs = glob.glob(os.path.join(DIAGRAM_DIR, diagram_folder, "*.png"))
                    if pngs:
                        meta["diagram"] = pngs[0]
                    else:
                        meta["diagram"] = None
            else:
                meta["diagram"] = None
            
            sites.append(meta)

    # Sort sites by name
    sites.sort(key=lambda x: x["site_name"])

    # Generate Markdown
    with open(OUTPUT_MD, "w") as f:
        f.write("# OzFlux Tower Network: Detailed Site Reports\n\n")
        f.write("## Introduction\n\n")
        f.write("OzFlux is a national network of flux towers that provides continuous measurements of carbon, water, and energy exchanges between terrestrial ecosystems and the atmosphere across Australia and New Zealand. This report provides a detailed overview of the tower sites, including their physical configurations and key metadata.\n\n")
        f.write(f"Total sites documented: {len(sites)}\n\n")
        f.write("---\n\n")

        for site in sites:
            if not site["diagram"]:
                continue

            f.write(f"## {site['site_name']}\n\n")
            # Use absolute path for pandoc
            f.write(f"![]({site['diagram']})\n\n")

            f.write("### Site Metadata\n\n")
            f.write("| Attribute | Value |\n")
            f.write("| --- | --- |\n")
            f.write(f"| **PI** | {site['site_pi']} |\n")
            f.write(f"| **Institution** | {site['institution']} |\n")
            f.write(f"| **Latitude** | {site['latitude']} |\n")
            f.write(f"| **Longitude** | {site['longitude']} |\n")
            f.write(f"| **Elevation** | {site['elevation']} |\n")
            f.write(f"| **Soil Type** | {site['soil']} |\n")
            f.write(f"| **Vegetation** | {site['vegetation']} |\n")
            f.write(f"| **Temporal Coverage** | {site['coverage']} |\n")
            f.write(f"| **Data Link** | [{site['data_link']}]({site['data_link']}) |\n\n")
            f.write("\\newpage\n\n")

    print(f"Markdown report generated: {OUTPUT_MD}")

if __name__ == "__main__":
    main()
