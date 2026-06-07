import os
import xarray as xr
import glob
from bs4 import BeautifulSoup

# Constants
METADATA_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6"
DIAGRAM_DIR = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/FluxTower_Diagrams"
OUTPUT_TEX = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/L6/soil_depth_plots/OzFlux_Tower_Report_Detailed.tex"
MIRROR_BASE = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/ozflux_mirror/www.ozflux.org.au/monitoringsites"

def clean_site_name(name):
    """Remove spaces and special characters for matching folder names."""
    return name.replace(" ", "").replace("-", "").replace("_", "")

def escape_latex(text):
    """Escape LaTeX special characters in plain text."""
    if not text:
        return ""
    # LaTeX special characters
    replacements = {
        '\\': '\\textbackslash{}',
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
    }
    # Sort keys by length in descending order to avoid partial replacement of escaped chars
    for key in sorted(replacements.keys(), key=len, reverse=True):
        text = text.replace(key, replacements[key])
    return text

def clean_unicode(text):
    """Clean unicode and apply LaTeX escaping to make text pdflatex-compatible."""
    if not text:
        return ""
    # Replace unicode replacement characters and non-ascii spaces
    text = text.replace('\ufffd', ' ')
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '') # zero-width space
    text = text.replace('\u2212', '-') # Unicode minus
    
    # Store degree symbol before general LaTeX escaping
    text = text.replace('°', 'TEMPDEGREE')
    
    # Escape standard LaTeX special characters
    text = escape_latex(text)
    
    # Re-insert degrees symbol as LaTeX math
    text = text.replace('TEMPDEGREE', '$^\\circ$')
    
    # Common superscripts and fractions
    text = text.replace('²', '$^2$')
    text = text.replace('³', '$^3$')
    text = text.replace('¹', '$^1$')
    text = text.replace('½', '1/2')
    text = text.replace('¼', '1/4')
    text = text.replace('¾', '3/4')
    
    # Common Greek letters and symbols
    text = text.replace('±', '$\\pm$')
    text = text.replace('×', '$\\times$')
    text = text.replace('α', '$\\alpha$')
    text = text.replace('β', '$\\beta$')
    text = text.replace('γ', '$\\gamma$')
    text = text.replace('δ', '$\\delta$')
    text = text.replace('θ', '$\\theta$')
    text = text.replace('μ', '$\\mu$')
    text = text.replace('σ', '$\\sigma$')
    text = text.replace('λ', '$\\lambda$')
    text = text.replace('π', '$\\pi$')
    text = text.replace('Ω', '$\\Omega$')
    text = text.replace('Δ', '$\\Delta$')
    text = text.replace('Φ', '$\\Phi$')
    
    return text

def get_metadata(nc_file):
    """Extract global attributes from a NetCDF file."""
    try:
        with xr.open_dataset(nc_file) as ds:
            attrs = ds.attrs
            return {
                "site_name": clean_unicode(attrs.get("site_name", "N/A")),
                "latitude": clean_unicode(str(attrs.get("latitude", "N/A"))),
                "longitude": clean_unicode(str(attrs.get("longitude", "N/A"))),
                "site_pi": clean_unicode(attrs.get("site_pi", "N/A")),
                "soil": clean_unicode(attrs.get("soil", "N/A")),
                "institution": clean_unicode(attrs.get("institution", "N/A")),
                "data_link": attrs.get("data_link", "N/A"), # will format separately as url
                "elevation": clean_unicode(str(attrs.get("elevation", "N/A"))),
                "vegetation": clean_unicode(attrs.get("vegetation", "N/A")),
                "coverage": clean_unicode(attrs.get("time_coverage_start", "N/A") + " to " + attrs.get("time_coverage_end", "N/A"))
            }
    except Exception as e:
        print(f"Error reading {nc_file}: {e}")
        return None

def get_site_web_details(site_name):
    # Convert name to lowercase and strip all punctuation/spaces
    clean = clean_site_name(site_name).lower()
    
    # Explicit mapping overrides
    exceptions = {
        "greatwesternwoodlands": "gww",
        "wombatstateforest1": "wombat",
        "wombatstateforest2": "wombat",
        "yarramundicontrol": "yarramundi",
        "yarramundiirrigated": "yarramundi",
        "alicespringsmulga1": "alicesprings",
        "alicespringsmulga2": "alicesprings",
        "dalypasture": "dalypasture",
        "dalyuncleared": "dalyuncleared",
        "foggdam": "foggdam",
        "howardsprings": "howardsprings",
        "adelaideriver": "adelaideriver",
        "alpinepeatland": "alpinepeatland",
        "capetribulation": "capetribulation",
        "cumberlandplain": "cumberlandplain",
        "robsoncreek": "robsoncreek",
        "samford": "samford",
        "silverplains": "silverplains",
        "sturtplains": "sturtplains",
        "titreeeast": "titreeeast",
        "tumbarumba": "tumbarumba",
        "wallabycreek": "wallabycreek",
        "warra": "warra",
        "whroo": "whroo",
        "yanco": "yanco",
        "otway": "otway",
        "gatumpasture": "gatumpasture",
        "gingin": "gingin",
        "collie": "collie",
        "cowbay": "cowbay",
        "ridgefield": "ridgefield",
        "riggscreek": "riggscreek",
    }
    
    folder_name = exceptions.get(clean, clean)
    site_dir = os.path.join(MIRROR_BASE, folder_name)
    
    if not os.path.exists(site_dir):
        # Try finding a sub-folder that starts with or matches
        matched = None
        for name in os.listdir(MIRROR_BASE):
            if os.path.isdir(os.path.join(MIRROR_BASE, name)):
                if clean.startswith(name) or name.startswith(clean):
                    matched = name
                    site_dir = os.path.join(MIRROR_BASE, name)
                    folder_name = name
                    break
        if not matched:
            return None, None
            
    return folder_name, site_dir

def clean_html_element_to_latex(elem):
    if elem.name == 'p':
        text = ""
        for child in elem.children:
            if child.name in ['strong', 'b']:
                text += f"\\textbf{{{clean_unicode(child.text.strip())}}}"
            elif child.name in ['em', 'i']:
                text += f"\\textit{{{clean_unicode(child.text.strip())}}}"
            elif child.name is None:
                text += clean_unicode(str(child))
            elif child.name == 'br':
                text += "\n\n"
            else:
                text += clean_unicode(child.text)
        return text
    elif elem.name in ['ul', 'ol']:
        items = []
        for li in elem.find_all('li'):
            li_text = ""
            for child in li.children:
                if child.name in ['strong', 'b']:
                    li_text += f"\\textbf{{{clean_unicode(child.text.strip())}}}"
                elif child.name in ['em', 'i']:
                    li_text += f"\\textit{{{clean_unicode(child.text.strip())}}}"
                elif child.name is None:
                    li_text += clean_unicode(str(child))
                else:
                    li_text += clean_unicode(child.text)
            if li_text.strip():
                items.append(f"  \\item {li_text.strip()}")
        if items:
            return "\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}"
        return ""
    elif elem.name in ['h3', 'h4']:
        return f"\\subsubsection*{{{clean_unicode(elem.text.strip())}}}"
    return clean_unicode(elem.text.strip())

def parse_html_content_latex(filepath):
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    panel = soup.find(class_='home_right_panel')
    if not panel:
        return ""
    
    content = []
    for elem in panel.children:
        if elem.name in ['p', 'ul', 'ol', 'h3', 'h4', 'div', 'table']:
            # Skip links bar
            if elem.find('a') and any(kw in elem.text.lower() for kw in ['introduction', 'purpose', 'description']):
                continue
            if elem.get('class') == ['paragraph_title']:
                continue
            if elem.name == 'table':
                continue
            text = clean_html_element_to_latex(elem)
            if text.strip():
                content.append(text.strip())
    return "\n\n".join(content)

def parse_measurements_latex(site_dir, site_key):
    meas_file = os.path.join(site_dir, f"{site_key}_measurements.html")
    if not os.path.exists(meas_file):
        return ""
    
    with open(meas_file, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        
    panel = soup.find(class_='home_right_panel')
    if not panel:
        return ""
        
    table = panel.find('table')
    if not table:
        return ""
        
    th_elements = table.find_all('th')
    if not th_elements:
        first_tr = table.find('tr')
        if first_tr:
            th_elements = first_tr.find_all(['td', 'th'])
            
    headers = [clean_unicode(th.text.strip().replace('\n', ' ')) for th in th_elements]
    if not headers:
        return ""
        
    # Build column spec based on column count
    num_cols = len(headers)
    if num_cols == 4:
        col_spec = "p{4.5cm}p{3.5cm}p{3.5cm}p{3.5cm}"
    elif num_cols == 3:
        col_spec = "p{5cm}p{5cm}p{5cm}"
    elif num_cols == 2:
        col_spec = "p{6cm}p{9cm}"
    else:
        col_spec = " ".join(["l"] * num_cols)
        
    latex = f"\\begin{{longtable}}{{{col_spec}}}\n"
    latex += "\\toprule\n"
    latex += " & ".join([f"\\textbf{{{h}}}" for h in headers]) + " \\\\\n"
    latex += "\\midrule\n"
    latex += "\\endhead\n"
    latex += "\\bottomrule\n"
    latex += "\\endfoot\n"
    
    row_count = 0
    for tr in table.find_all('tr'):
        if tr.find('th'):
            continue
        tds = tr.find_all('td')
        if not tds:
            continue
        # Skip header duplicate rows
        if [td.text.strip() for td in tds] == [h.replace('\\', '').replace('$', '').replace('^', '').replace('{', '').replace('}', '') for h in headers]:
            continue
            
        cols = [clean_unicode(td.text.strip().replace('\n', ' ')) for td in tds]
        if len(cols) == num_cols:
            latex += " & ".join(cols) + " \\\\\n"
            row_count += 1
            
    latex += "\\end{longtable}\n"
    
    if row_count == 0:
        return ""
    return latex

def parse_pictures(site_dir, site_key):
    pics_file = os.path.join(site_dir, f"{site_key}_pictures.html")
    if not os.path.exists(pics_file):
        return []

    with open(pics_file, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    panel = soup.find(class_='home_right_panel')
    if not panel:
        return []
        
    pics = []
    for img in panel.find_all('img'):
        src = img.get('src')
        if not src:
            continue
        abs_img_path = os.path.abspath(os.path.join(site_dir, src))
        if os.path.exists(abs_img_path):
            caption = ""
            parent_td = img.find_parent('td')
            if parent_td:
                p_tags = parent_td.find_all('p')
                for p in p_tags:
                    if not p.find('img'):
                        caption = p.text.strip()
                        break
                if not caption:
                    caption = parent_td.text.strip()
            else:
                caption = img.get('alt', '')
            
            caption = caption.replace('\n', ' ').strip()
            if not caption:
                caption = img.get('alt', 'Site Image')
            pics.append({
                "path": abs_img_path,
                "caption": clean_unicode(caption)
            })
    return pics

def generate_metadata_table_latex(site):
    latex = "\\begin{longtable}{p{4.5cm}p{10.5cm}}\n"
    latex += "\\toprule\n"
    latex += "\\textbf{Attribute} & \\textbf{Value} \\\\\n"
    latex += "\\midrule\n"
    latex += "\\endhead\n"
    latex += "\\bottomrule\n"
    latex += "\\endfoot\n"
    
    # Securely handle data link formatting
    link = site['data_link']
    if link != 'N/A' and link.startswith('http'):
        formatted_link = f"\\url{{{link}}}"
    else:
        formatted_link = escape_latex(link)
        
    attributes = [
        ("PI", site['site_pi']),
        ("Institution", site['institution']),
        ("Latitude", site['latitude']),
        ("Longitude", site['longitude']),
        ("Elevation", site['elevation']),
        ("Soil Type", site['soil']),
        ("Vegetation", site['vegetation']),
        ("Temporal Coverage", site['coverage']),
        ("Data Link", formatted_link)
    ]
    
    for attr, val in attributes:
        latex += f"\\textbf{{{attr}}} & {val} \\\\\n"
        
    latex += "\\end{longtable}\n"
    return latex

def main():
    nc_files = glob.glob(os.path.join(METADATA_DIR, "*_L6_Summary.nc"))
    sites = []

    for nc in nc_files:
        meta = get_metadata(nc)
        if meta:
            # Match with diagram
            site_key = clean_site_name(meta["site_name"])
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
                    pngs = glob.glob(os.path.join(DIAGRAM_DIR, diagram_folder, "*.png"))
                    if pngs:
                        meta["diagram"] = pngs[0]
                    else:
                        meta["diagram"] = None
            else:
                meta["diagram"] = None
            
            # Match with web content
            folder_name, site_web_dir = get_site_web_details(meta["site_name"])
            if folder_name and site_web_dir:
                meta["web_folder"] = folder_name
                meta["web_dir"] = site_web_dir
                
                # Parse web content
                meta["description"] = parse_html_content_latex(os.path.join(site_web_dir, f"{folder_name}_description.html"))
                meta["purpose"] = parse_html_content_latex(os.path.join(site_web_dir, f"{folder_name}_purpose.html"))
                meta["measurements"] = parse_measurements_latex(site_web_dir, folder_name)
                meta["photos"] = parse_pictures(site_web_dir, folder_name)
            else:
                meta["web_folder"] = None
                meta["web_dir"] = None
                meta["description"] = ""
                meta["purpose"] = ""
                meta["measurements"] = ""
                meta["photos"] = []
            
            sites.append(meta)

    # Sort sites by name
    sites.sort(key=lambda x: x["site_name"])

    # Write LaTeX document
    with open(OUTPUT_TEX, "w", encoding='utf-8') as f:
        # Preamble
        f.write("\\documentclass[11pt,a4paper]{article}\n")
        f.write("\\usepackage[utf8]{inputenc}\n")
        f.write("\\usepackage[margin=1in]{geometry}\n")
        f.write("\\usepackage{graphicx}\n")
        f.write("\\usepackage{longtable}\n")
        f.write("\\usepackage{booktabs}\n")
        f.write("\\usepackage{hyperref}\n")
        f.write("\\usepackage{array}\n")
        f.write("\\usepackage{fancyhdr}\n")
        f.write("\\usepackage{amsmath}\n")
        f.write("\\usepackage{titlesec}\n")
        f.write("\\usepackage{color}\n")
        f.write("\\usepackage{float}\n")
        f.write("\\usepackage{caption}\n")
        f.write("\\usepackage{microtype}\n\n")
        
        # Header/Footer Setup
        f.write("\\pagestyle{fancy}\n")
        f.write("\\fancyhf{}\n")
        f.write("\\fancyhead[L]{OzFlux Tower Network: Detailed Site Reports}\n")
        f.write("\\fancyhead[R]{\\thepage}\n")
        f.write("\\fancyfoot[C]{Confidential - Research Use Only}\n")
        f.write("\\renewcommand{\\headrulewidth}{0.4pt}\n")
        f.write("\\renewcommand{\\footrulewidth}{0pt}\n\n")
        
        # Document Start
        f.write("\\begin{document}\n\n")
        
        # Title Page
        f.write("\\title{\\textbf{OzFlux Tower Network: Detailed Site Reports (V2)}}\n")
        f.write("\\author{OzFlux Team}\n")
        f.write("\\date{\\today}\n")
        f.write("\\maketitle\n\n")
        
        f.write("\\begin{abstract}\n")
        f.write("OzFlux is a national network of flux towers that provides continuous measurements of carbon, water, and energy exchanges between terrestrial ecosystems and the atmosphere across Australia and New Zealand. This detailed report merges physical configuration diagrams, scientific purposes, site descriptions, instrument tables, and on-site photographs to document each monitoring station.\n")
        f.write("\\end{abstract}\n\n")
        
        f.write(f"Total sites documented: {len([s for s in sites if s['diagram']])}\n\n")
        f.write("\\newpage\n\n")
        
        # Table of Contents
        f.write("\\tableofcontents\n")
        f.write("\\newpage\n\n")

        for site in sites:
            # Skip if diagram not found (per user instruction)
            if not site["diagram"]:
                continue
                
            f.write(f"\\section{{Site Profile: {site['site_name']}}}\n\n")
            
            # 1. Tower Diagram
            f.write("\\subsection*{Physical Configuration \\& Soil Sensor Depths}\n\n")
            f.write("\\begin{figure}[H]\n")
            f.write("\\centering\n")
            # Limit width and height to keep layout clean and page-break aligned
            f.write(f"  \\includegraphics[width=0.85\\textwidth,height=0.45\\textheight,keepaspectratio]{{{site['diagram']}}}\n")
            f.write("  \\caption*{Soil sensor depth profile and tower instrument heights.}\n")
            f.write("\\end{figure}\n\n")
            f.write("\\newpage\n\n")

            # 2. Site Description
            if site["description"]:
                f.write("\\subsection*{Site Description}\n\n")
                f.write(f"{site['description']}\n\n")

            # 3. Site Purpose
            if site["purpose"]:
                f.write("\\subsection*{Purpose \\& Scientific Goals}\n\n")
                f.write(f"{site['purpose']}\n\n")

            # 4. Photos (if any)
            if site["photos"]:
                f.write("\\subsection*{Site Photographs}\n\n")
                for idx, photo in enumerate(site["photos"]):
                    f.write("\\begin{figure}[H]\n")
                    f.write("\\centering\n")
                    f.write(f"  \\includegraphics[width=0.8\\textwidth,height=0.4\\textheight,keepaspectratio]{{{photo['path']}}}\n")
                    f.write(f"  \\caption*{{Photo {idx+1}: {photo['caption']}}}\n")
                    f.write("\\end{figure}\n\n")

            # 5. Measurements (if any)
            if site["measurements"]:
                f.write("\\subsection*{Measurement Instrumentation}\n\n")
                f.write(f"{site['measurements']}\n\n")

            # 6. Global Metadata Table
            f.write("\\subsection*{Tower Global Metadata}\n\n")
            f.write(generate_metadata_table_latex(site))
            f.write("\n")
            
            f.write("\\newpage\n\n")

        f.write("\\end{document}\n")

    print(f"LaTeX report code generated successfully: {OUTPUT_TEX}")

if __name__ == "__main__":
    main()
