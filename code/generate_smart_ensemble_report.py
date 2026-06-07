import os
import pandas as pd
import subprocess

# Define base directory
base_dir = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/PET_Results_SmartEnsemble"
summary_path = os.path.join(base_dir, "Summary.csv")

def tex_escape(text):
    if not isinstance(text, str):
        return str(text)
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for key, val in replacements.items():
        text = text.replace(key, val)
    return text

# Read Summary
df_summary = pd.read_csv(summary_path)

# Start generating LaTeX code
latex = []
latex.append(r"\documentclass[11pt,a4paper]{article}")
latex.append(r"\usepackage[utf8]{inputenc}")
latex.append(r"\usepackage[margin=0.7in]{geometry}")
latex.append(r"\usepackage{booktabs}")
latex.append(r"\usepackage{graphicx}")
latex.append(r"\usepackage{float}")
latex.append(r"\usepackage{hyperref}")
latex.append(r"\usepackage{amsmath}")
latex.append(r"\usepackage{caption}")
latex.append(r"\usepackage{subcaption}")
latex.append(r"\usepackage{fancyhdr}")
latex.append(r"\usepackage{longtable}")

latex.append(r"\pagestyle{fancy}")
latex.append(r"\fancyhf{}")
latex.append(r"\fancyhead[L]{PET Formulation Rankings \& Validation}")
latex.append(r"\fancyhead[R]{IITB-Monash Research Academy}")
latex.append(r"\fancyfoot[C]{\thepage}")

latex.append(r"\begin{document}")

# Title Page
latex.append(r"\begin{titlepage}")
latex.append(r"\centering")
latex.append(r"\vspace*{2cm}")
latex.append(r"{\Huge\bfseries Smart Evapotranspiration Ensemble:\par}")
latex.append(r"\vspace{0.5cm}")
latex.append(r"{\Large\bfseries Potential Evapotranspiration (PET) Formulation Rankings and Validation across 41 OzFlux Sites\par}")
latex.append(r"\vspace{1.5cm}")
latex.append(r"{\large\bfseries Sanjay N C\par}")
latex.append(r"{\large Ph.D. Student, IITB-Monash Research Academy\par}")
latex.append(r"{\large Emails: sanjaync@iitb.ac.in, sanjaync@monash.edu\par}")
latex.append(r"\vspace{1cm}")
latex.append(r"{\large\today\par}")
latex.append(r"\vspace{2cm}")
latex.append(r"\begin{abstract}")
latex.append(r"This report presents a comprehensive cross-validation of 18 different potential evapotranspiration (PET) formulations against the Penman-Monteith ASCE combination reference benchmark across 41 OzFlux eddy-covariance sites. Evaluation metrics including the Kling-Gupta Efficiency (KGE), coefficient of determination ($R^2$), root mean square error (RMSE), and bias are compiled programmatically to rank methods and select the Top-5 best performing formulations for each site. The results serve as a calibration foundation for the Stochastic Soil Water Model (SSWM) and Eco-Evolutionary Optimality (EEO) pipelines across Australian ecosystems.")
latex.append(r"\end{abstract}")
latex.append(r"\end{titlepage}")

latex.append(r"\tableofcontents")
latex.append(r"\newpage")

# Section 1: Methodology
latex.append(r"\section{Introduction \& Methodology}")
latex.append(r"Accurate estimation of potential evapotranspiration (PET) is critical for diagnosing soil moisture dynamics and vegetation water-use strategies. In this study, we evaluated 18 temperature-based, radiation-based, and combination-based PET formulations against the standard Penman-Monteith (ASCE) combination reference model across 41 eddy-covariance sites in Australia. Evaluation metrics are defined as follows:")
latex.append(r"\begin{itemize}")
latex.append(r"\item \textbf{Kling-Gupta Efficiency (KGE)}: An objective function that combines correlation, variability, and bias components.")
latex.append(r"\item \textbf{Coefficient of Determination ($R^2$)}: Measures the proportion of variance explained by each formulation.")
latex.append(r"\item \textbf{Root Mean Square Error (RMSE)}: Quantifies the absolute prediction error magnitude (mm/day).")
latex.append(r"\item \textbf{Bias}: Quantifies systemic over- or under-estimation (mm/day).")
latex.append(r"\end{itemize}")
latex.append(r"At each site, methods are ranked in descending order of KGE. The Top-5 formulations are then selected to build a site-specific consensus ensemble forcing.")

# Section 2: Summary Table
latex.append(r"\section{Summary of Top Performing Formulations}")
latex.append(r"Table \ref{tab:overall_summary} lists the primary geographic characteristics (latitude, elevation, and vegetation cover) for all 41 sites alongside the best-performing (Rank 1, excluding benchmark) PET method and its corresponding KGE value.")

latex.append(r"\begin{longtable}{llccp{2.5in}cc}")
latex.append(r"\caption{Geographic details and top-ranked PET formulation performance for 41 OzFlux sites.} \label{tab:overall_summary} \\")
latex.append(r"\toprule")
latex.append(r"Site ID & Latitude & Elevation (m) & Vegetation & Best PET Method & KGE \\")
latex.append(r"\midrule")
latex.append(r"\endhead")
latex.append(r"\bottomrule")
latex.append(r"\endfoot")

# Populate Summary Table and verify directories
site_metrics_cache = {}
for idx, row in df_summary.iterrows():
    site_id = row['site']
    lat = f"{row['lat']:.4f}" if not pd.isna(row['lat']) else "N/A"
    elev = f"{row['elev']:.1f}" if not pd.isna(row['elev']) else "N/A"
    veg = tex_escape(row['veg']) if not pd.isna(row['veg']) else "N/A"
    
    # Load site ranked metrics
    site_csv = os.path.join(base_dir, site_id, f"PET_{site_id}_Metrics_Ranked.csv")
    best_method = "N/A"
    best_kge = "N/A"
    if os.path.exists(site_csv):
        try:
            df_m = pd.read_csv(site_csv)
            # Remove reference pm_asce if present
            df_m_clean = df_m[df_m['Method'] != 'pm_asce'].copy()
            if len(df_m_clean) > 0:
                top_row = df_m_clean.iloc[0]
                best_method = tex_escape(top_row['Method'])
                best_kge = f"{top_row['KGE']:.3f}"
                site_metrics_cache[site_id] = df_m_clean.head(5)
        except Exception as e:
            print(f"Error loading {site_csv}: {e}")
            
    latex.append(f"{tex_escape(site_id)} & {lat} & {elev} & {veg} & {best_method} & {best_kge} \\\\")

latex.append(r"\end{longtable}")
latex.append(r"\newpage")

# Section 3: Site by Site Detailed Appendix
latex.append(r"\section{Site-by-Site Formulation Rankings and Visualizations}")
latex.append(r"This appendix presents the site-specific vegetation information, the Top-5 ranked PET formulations, and visual verification plots (diurnal/seasonal full record series and performance matrix heatmaps) for each of the 41 sites.")

for idx, row in df_summary.iterrows():
    site_id = row['site']
    veg = tex_escape(row['veg']) if not pd.isna(row['veg']) else "N/A"
    elev = f"{row['elev']:.1f}" if not pd.isna(row['elev']) else "N/A"
    lat = f"{row['lat']:.4f}" if not pd.isna(row['lat']) else "N/A"
    
    latex.append(r"\subsection{" + tex_escape(site_id) + r"}")
    latex.append(f"\\textbf{{Geographic Metadata:}} Latitude: {lat}$^\circ$, Elevation: {elev} m, Vegetation Type: {veg}.\n")
    latex.append(r"\vspace{0.2cm}")
    
    # Table of Top 5
    if site_id in site_metrics_cache:
        df_top5 = site_metrics_cache[site_id]
        latex.append(r"\begin{table}[H]")
        latex.append(r"\centering")
        latex.append(f"\\caption{{Top-5 Ranked PET Formulations for {tex_escape(site_id)}.}}")
        latex.append(r"\begin{tabular}{llcccc}")
        latex.append(r"\toprule")
        latex.append(r"Rank & Method & KGE & $R^2$ & RMSE (mm/d) & Bias (mm/d) \\")
        latex.append(r"\midrule")
        for rank, (_, m_row) in enumerate(df_top5.iterrows(), 1):
            method = tex_escape(m_row['Method'])
            kge = f"{m_row['KGE']:.3f}" if not pd.isna(m_row['KGE']) else "N/A"
            r2 = f"{m_row['R2']:.3f}" if not pd.isna(m_row['R2']) else "N/A"
            rmse = f"{m_row['RMSE']:.3f}" if not pd.isna(m_row['RMSE']) else "N/A"
            bias = f"{m_row['Bias']:.3f}" if not pd.isna(m_row['Bias']) else "N/A"
            latex.append(f"{rank} & {method} & {kge} & {r2} & {rmse} & {bias} \\\\")
        latex.append(r"\bottomrule")
        latex.append(r"\end{tabular}")
        latex.append(r"\end{table}")
    
    # Insert Plots
    plot_full = f"./{site_id}/plots/00_{site_id}_Full_Record.png"
    plot_matrix = f"./{site_id}/plots/05_{site_id}_Performance_Matrix.png"
    
    if os.path.exists(os.path.join(base_dir, plot_full)) or os.path.exists(os.path.join(base_dir, plot_matrix)):
        latex.append(r"\begin{figure}[H]")
        latex.append(r"\centering")
        if os.path.exists(os.path.join(base_dir, plot_full)):
            latex.append(r"\begin{subfigure}[b]{0.65\textwidth}")
            latex.append(r"\centering")
            latex.append(r"\includegraphics[width=\textwidth]{" + plot_full + r"}")
            latex.append(r"\caption{Comparison of daily timeseries over the full record.}")
            latex.append(r"\end{subfigure}")
        if os.path.exists(os.path.join(base_dir, plot_matrix)):
            latex.append(r"\begin{subfigure}[b]{0.32\textwidth}")
            latex.append(r"\centering")
            latex.append(r"\includegraphics[width=\textwidth]{" + plot_matrix + r"}")
            latex.append(r"\caption{Performance evaluation matrix.}")
            latex.append(r"\end{subfigure}")
        latex.append(f"\\caption{{Visual diagnostics and performance evaluation for {tex_escape(site_id)}.}}")
        latex.append(r"\end{figure}")
        
    latex.append(r"\newpage")

latex.append(r"\end{document}")

# Write to file
tex_output_path = os.path.join(base_dir, "PET_SmartEnsemble_Report.tex")
with open(tex_output_path, "w") as f:
    f.write("\n".join(latex))

print(f"LaTeX file written to: {tex_output_path}")

# Compile
print("Compiling LaTeX report...")
try:
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "PET_SmartEnsemble_Report.tex"], cwd=base_dir, check=True)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "PET_SmartEnsemble_Report.tex"], cwd=base_dir, check=True)
    print("SUCCESS! PDF report compiled.")
except Exception as e:
    print(f"Failed to compile LaTeX: {e}")
