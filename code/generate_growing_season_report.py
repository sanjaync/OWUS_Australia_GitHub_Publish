import os
import subprocess
import shutil

# Paths
base_dir_baseline = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/FINAL_PAPER_BUNDLE"
base_dir_ensemble = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_ensemble_top5/FINAL_PAPER_BUNDLE_ENSEMBLE"

# All 17 selected sites (including AU-Alp, AU-Fog, AU-Wal as requested)
seasonal_sites = [
    'AU-Adr', 'AU-Alp', 'AU-Ctr', 'AU-DaP', 'AU-Eme', 
    'AU-Fog', 'AU-Gat', 'AU-Gre', 'AU-Lit', 'AU-RDF', 
    'AU-Rgf', 'AU-SiP', 'AU-Stp', 'AU-Wal', 'AU-Whr', 
    'AU-YarI', 'AU-Ync'
]

site_metadata = {
    'AU-Adr': {'name': 'Adelaide River', 'igbp': 'GRA', 'desc': 'Open forest/savanna site located in the Northern Territory, experiencing a distinct monsoonal wet-dry climate.'},
    'AU-Alp': {'name': 'Alice Springs Mulga', 'igbp': 'ENF', 'desc': 'Arid grassland and Mulga (Acacia aneura) woodland site in central Northern Territory. Characterized by low, highly episodic rainfall and extreme temperatures.'},
    'AU-Ctr': {'name': 'Calperum Chowilla', 'igbp': 'EBF', 'desc': 'Mallee woodland and shrubland site in South Australia. Semi-arid zone with highly variable rainfall.'},
    'AU-DaP': {'name': 'Daly River Cleared', 'igbp': 'GRA', 'desc': 'Tropical pasture/grassland site in the Northern Territory, undergoing intense seasonal wet-dry transitions.'},
    'AU-Eme': {'name': 'Emerald', 'igbp': 'GRA', 'desc': 'Dry tropical agricultural grassland/pasture site in Queensland, with summer-dominant rainfall.'},
    'AU-Fog': {'name': 'Fogg Dam', 'igbp': 'GRA', 'desc': 'Humid tropical flood plain and wetland site in the Northern Territory. Dominated by dense grasslands/forests that remain wet for long periods of the year.'},
    'AU-Gat': {'name': 'Gatton', 'igbp': 'GRA', 'desc': 'Agricultural crop and pasture site in Queensland, situated in a sub-tropical clay-soil zone.'},
    'AU-Gre': {'name': 'Great Victoria Desert', 'igbp': 'SAV', 'desc': 'Arid savanna site in Western Australia, characterized by hummock grasslands and sparse shrubs.'},
    'AU-Lit': {'name': 'Litchfield', 'igbp': 'SAV', 'desc': 'Tropical savanna site in the Northern Territory, dominated by Eucalyptus forest and grass understory.'},
    'AU-RDF': {'name': 'Red Dirt Melon Farm', 'igbp': 'GRA', 'desc': 'Cleared pasture site in the Northern Territory with a highly seasonal monsoonal climate.'},
    'AU-Rgf': {'name': 'Ridgefield', 'igbp': 'CRO', 'desc': 'Mediterranean cropland site in Western Australia, experiencing wet winters and dry summers.'},
    'AU-SiP': {'name': 'Silver Plains', 'igbp': 'WSA', 'desc': 'Woody savanna site in Cape York, Queensland, subject to intense tropical wet and dry periods.'},
    'AU-Stp': {'name': 'Sturt Plains', 'igbp': 'GRA', 'desc': 'Cracking clay grassland site in the Northern Territory, undergoing extreme seasonal inundation and dry-down.'},
    'AU-Wal': {'name': 'Wallaby Creek', 'igbp': 'EBF', 'desc': 'Wet sclerophyll eucalyptus forest in Victoria. Located in a temperate mountainous region with high rainfall and deep clay loam soils.'},
    'AU-Whr': {'name': 'Whroo', 'igbp': 'WSA', 'desc': 'Dry temperate eucalyptus woodland site in Victoria, with winter-dominant rainfall.'},
    'AU-YarI': {'name': 'Yanco Agricultural', 'igbp': 'GRA', 'desc': 'Agricultural grassland site in semi-arid New South Wales, subject to seasonal cropping.'},
    'AU-Ync': {'name': 'Yanco Grassland', 'igbp': 'GRA', 'desc': 'Native grassland site in semi-arid New South Wales, with high inter-annual volatility.'}
}

def generate_latex():
    latex_code = []
    
    # Preamble
    latex_code.append(r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{float}
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{caption}
\usepackage{microtype}
\geometry{margin=1in}

\title{\textbf{Comparative Analysis of Ecosystem Growing Season Dynamics:\\ Priestley-Taylor Baseline vs. Multi-Physics Ensemble PET Forcing}}
\author{\textbf{Sanjay S.} \\ Department of Civil Engineering, Monash University, Australia \\ \texttt{sanjays@monash.edu}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
The extraction of annual growing seasons and dry-down trajectories provides a critical test for physiological thresholds in ecohydrological models. This report catalogs the observed and simulated growing season dynamics across all 17 selected OzFlux sites under two atmospheric demand configurations: the single-physics Priestley-Taylor (PT) baseline and the multi-physics Ensemble Top-5 Mean PET. While 14 sites show distinct seasonal wet-dry patterns, 3 sites (AU-Alp, AU-Fog, and AU-Wal) are characterized by non-seasonal, flooded, or continuously wet evergreen vegetation dynamics, for which traditional dry-down cycles are not extracted. We present top-and-bottom comparisons of the soil moisture drawdowns and physiological stress responses for seasonal sites, and provide detailed physiological notes for the non-seasonal sites, offering key insights into model boundary condition sensitivities.
\end{abstract}

\section{Introduction and Site Classification}
The seasonal cycle of water availability in Australian ecosystems is highly volatile. To evaluate how potential evapotranspiration (PET) formulations affect soil water extraction during active vegetation growth, we isolate individual growing seasons. These periods are defined from the initiation of wet-season green-up through the post-wet season dry-down phase.

Of the 17 selected sites in our core dataset, three are classified as non-seasonal or non-extractable:
\begin{enumerate}
    \item \textbf{AU-Alp} (Alice Springs Mulga): Characterized by episodic, opportunistic vegetation activity driven by irregular rainfall pulses in an arid environment, rather than a regular annual seasonal cycle.
    \item \textbf{AU-Fog} (Fogg Dam): A flooded wetland where soil moisture remains saturated or near-saturated for much of the year, preventing standard soil moisture dry-down extraction.
    \item \textbf{AU-Wal} (Wallaby Creek): A wet temperate evergreen forest with high rainfall and deep clay loam soils, maintaining continuous transpiration and high soil moisture levels without a distinct seasonal senescence or dry-down cycle.
\end{enumerate}

The remaining 14 sites represent seasonal grasslands, savannas, croplands, and mallee woodlands. For each of these seasonal sites, we compare the simulated growing season soil moisture and transpiration drawdowns under Priestley-Taylor forcing against those simulated under the Top-5 Ensemble Mean forcing. For the 3 non-seasonal sites, we document their local environmental features.

\newpage
\section{Individual Site Growing Season Comparison Catalog}
For the seasonal sites below, we present the growing season plot from the Priestley-Taylor Baseline configuration (top) and the Ensemble PET configuration (bottom). For the three non-seasonal sites (AU-Alp, AU-Fog, and AU-Wal), we provide a summary of their ecohydrological characteristics.

\newpage
""")
    
    # Catalog loop
    for site in seasonal_sites:
        name = site_metadata[site]['name']
        igbp = site_metadata[site]['igbp']
        desc = site_metadata[site]['desc']
        
        latex_code.append(r"\subsection{" + f"{site} --- {name} ({igbp})" + r"}")
        latex_code.append(desc)
        latex_code.append(r"\vskip 1em")
        
        if site in ['AU-Alp', 'AU-Fog', 'AU-Wal']:
            # Non-seasonal sites - display an elegant text box instead of plots
            latex_code.append(r"""\begin{center}
\begin{minipage}{0.95\textwidth}
\hrule
\vskip 0.5em
\noindent\textbf{Note on Growing Season Analysis:} This site is classified as \textbf{non-seasonal} or \textbf{non-extractable} within the SSWM dry-down framework. Consequently, growing season figures are not generated. Below is the physiological reasoning:
\begin{itemize}
""")
            if site == 'AU-Alp':
                latex_code.append(r"""    \item \textbf{Episodic Vegetation Activity}: Located in the central Australian arid zone, the Mulga (\textit{Acacia aneura}) vegetation does not follow a regular annual phenological cycle. Transpiration and growth occur in transient, opportunistic pulses immediately following highly episodic rainfall events.
    \item \textbf{Absence of Annual Dry-Down}: Because dry-down phases depend entirely on unpredictable convective rains rather than a fixed monsoonal or temperate cycle, standard calendar-based growing season extraction is mathematically invalid.
""")
            elif site == 'AU-Fog':
                latex_code.append(r"""    \item \textbf{Hydrologic Inundation}: As a tropical wetland/floodplain, the water table remains above or near the soil surface for much of the wet season and early dry season.
    \item \textbf{Saturated Soil Column}: The soil moisture content ($s$) stays saturated ($s \approx 1$) for extended periods. Transpiration is driven by radiation and energy availability rather than soil moisture limitations, making the soil moisture drawdown curve flat and non-extractable.
""")
            elif site == 'AU-Wal':
                latex_code.append(r"""    \item \textbf{Perennial Water Access}: Located in a high-rainfall, mountainous temperate zone, Wallaby Creek is dominated by giant Mountain Ash (\textit{Eucalyptus regnans}) trees with deep root networks in clay loam soils.
    \item \textbf{Continuous Transpiration}: The trees maintain active transpiration throughout the year, buffer seasonal moisture changes using deep-soil stores, and do not experience leaf senescence, preventing the extraction of a distinct seasonal dry-down.
""")
            latex_code.append(r"""\end{itemize}
\vskip 0.5em
\hrule
\end{minipage}
\end{center}
""")
        else:
            # Seasonal sites - display figures
            bf_fig = os.path.join(base_dir_baseline, f"03_Growing_Seasons/{site}_gs.png")
            ens_fig = os.path.join(base_dir_ensemble, f"03_Growing_Seasons/{site}_gs.png")
            
            # PT Figure
            latex_code.append(r"\begin{figure}[H]")
            latex_code.append(r"\centering")
            latex_code.append(f"\\includegraphics[width=0.72\\textwidth]{{{bf_fig}}}")
            latex_code.append(f"\\caption{{Priestley-Taylor Baseline growing season dynamics for {site}.}}")
            latex_code.append(f"\\label{{fig:gs_pt_{site}}}")
            latex_code.append(r"\end{figure}")
            
            # Ensemble Figure
            latex_code.append(r"\begin{figure}[H]")
            latex_code.append(r"\centering")
            latex_code.append(f"\\includegraphics[width=0.72\\textwidth]{{{ens_fig}}}")
            latex_code.append(f"\\caption{{Ensemble Top-5 PET growing season dynamics for {site}.}}")
            latex_code.append(f"\\label{{fig:gs_ens_{site}}}")
            latex_code.append(r"\end{figure}")
            
        latex_code.append(r"\newpage")
        
    latex_code.append(r"\end{document}")
    
    tex_content = "\n".join(latex_code)
    
    # Write to baseline directory
    tex_path_bl = os.path.join(base_dir_baseline, "growing_season_report.tex")
    with open(tex_path_bl, "w") as f:
        f.write(tex_content)
    print(f"Wrote LaTeX source to {tex_path_bl}")
    return tex_path_bl

def compile_pdf(tex_path):
    print("Compiling PDF...")
    try:
        # Run pdflatex twice
        for i in range(2):
            print(f"LaTeX run {i+1}/2...")
            res = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path],
                cwd=base_dir_baseline,
                capture_output=True,
                text=True
            )
            if res.returncode != 0:
                print(f"Error on run {i+1}:")
                print(res.stderr)
                print(res.stdout[-1000:])
                return False
        
        pdf_path_bl = os.path.join(base_dir_baseline, "growing_season_report.pdf")
        print(f"PDF compiled successfully! Saved at: {pdf_path_bl}")
        
        # Copy script and outputs to ensemble directory for completeness
        shutil.copy2(tex_path, os.path.join(base_dir_ensemble, "growing_season_report_ensemble.tex"))
        shutil.copy2(pdf_path_bl, os.path.join(base_dir_ensemble, "growing_season_report_ensemble.pdf"))
        print("Successfully copied reports to the Ensemble folder.")
        
        return True
    except Exception as e:
        print(f"Compilation exception: {e}")
        return False

if __name__ == "__main__":
    tex_file = generate_latex()
    compile_pdf(tex_file)
