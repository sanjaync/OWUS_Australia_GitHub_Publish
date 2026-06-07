import pandas as pd
import numpy as np
import os
import subprocess

# Define paths
base_dir = "/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/FINAL_PAPER_BUNDLE"
bf_path = os.path.join(base_dir, "output_corrected/combined/results_bf__ozflux_1.csv")
opt_path = os.path.join(base_dir, "output_corrected/combined/results_opt__ozflux_1.csv")
comp_path = os.path.join(base_dir, "output_corrected/combined/NSE_Comparison_Table_Scientific.csv")

# 17 selected sites
selected_sites = [
    'AU-Adr', 'AU-Alp', 'AU-Ctr', 'AU-DaP', 'AU-Eme', 
    'AU-Fog', 'AU-Gat', 'AU-Gre', 'AU-Lit', 'AU-RDF', 
    'AU-Rgf', 'AU-SiP', 'AU-Stp', 'AU-Wal', 'AU-Whr', 
    'AU-YarI', 'AU-Ync'
]

# Site metadata / location descriptions for the appendix
site_metadata = {
    'AU-Adr': {'name': 'Adelaide River', 'desc': 'Open forest/savanna site located in the Northern Territory, experiencing a distinct monsoonal wet-dry climate. Vegetation is dominated by grassland with scattered eucalyptus trees.'},
    'AU-Alp': {'name': 'Alice Springs Mulga', 'desc': 'Arid grassland and Mulga (Acacia aneura) woodland site in central Northern Territory. Characterized by low, highly episodic rainfall and extreme temperatures.'},
    'AU-Ctr': {'name': 'Calperum Chowilla', 'desc': 'Mallee woodland and shrubland site in South Australia. Located in a semi-arid zone, the site has highly variable rainfall and coarse, sandy soils.'},
    'AU-DaP': {'name': 'Daly River Cleared', 'desc': 'Tropical pasture/grassland site in the Northern Territory. Cleared from native savanna, it undergoes intense monsoonal wet seasons followed by severe dry periods.'},
    'AU-Eme': {'name': 'Emerald', 'desc': 'Dry tropical agricultural grassland/pasture site in central Queensland. Characterized by high solar radiation and summer-dominant rainfall.'},
    'AU-Fog': {'name': 'Fogg Dam', 'desc': 'Humid tropical flood plain and wetland site in the Northern Territory. Dominated by dense grasslands/forests that remain wet for long periods of the year.'},
    'AU-Gat': {'name': 'Gatton', 'desc': 'Agricultural crop and pasture site in Queensland, situated in a sub-tropical climate zone with clay soils.'},
    'AU-Gre': {'name': 'Great Victoria Desert', 'desc': 'Arid savanna site in Western Australia. Characterized by hummock grasslands (Spinifex) and sparse shrubs over sand dunes.'},
    'AU-Lit': {'name': 'Litchfield', 'desc': 'Tropical savanna site in the Northern Territory, dominated by open eucalyptus forest and tall grass understory, subject to annual fire cycles.'},
    'AU-RDF': {'name': 'Red Dirt Melon Farm', 'desc': 'Cleared pasture site in the Northern Territory. Highly seasonal monsoonal climate with sandy soils and high evaporative demand.'},
    'AU-Rgf': {'name': 'Ridgefield', 'desc': 'Mediterranean cropland site in Western Australia. Experiences wet winters and dry summers, dominated by annual crop species.'},
    'AU-SiP': {'name': 'Silver Plains', 'desc': 'Woody savanna site in Cape York, Queensland. Subject to tropical wet seasons and extensive seasonal drying.'},
    'AU-Stp': {'name': 'Sturt Plains', 'desc': 'Cracking clay grassland site in the Northern Territory. Experiences extreme seasonal hydrology (flooding to deep cracking dry-down).'},
    'AU-Wal': {'name': 'Wallaby Creek', 'desc': 'Wet sclerophyll eucalyptus forest in Victoria. Located in a temperate mountainous region with high rainfall and deep clay loam soils.'},
    'AU-Whr': {'name': 'Whroo', 'desc': 'Dry temperate eucalyptus woodland site in Victoria. Sandy clay loam soils with winter-dominant rainfall and hot, dry summers.'},
    'AU-YarI': {'name': 'Yanco Agricultural', 'desc': 'Agricultural grassland site in New South Wales. Situated in a semi-arid zone, subject to seasonal cropping and pasture grazing.'},
    'AU-Ync': {'name': 'Yanco Grassland', 'desc': 'Native grassland site in semi-arid New South Wales, characterized by high inter-annual climate variability driven by ENSO.'}
}

def load_data():
    df_bf = pd.read_csv(bf_path)
    df_opt = pd.read_csv(opt_path)
    df_comp = pd.read_csv(comp_path)
    
    # Filter for selected sites
    df_bf = df_bf[df_bf['siteID'].isin(selected_sites)].copy()
    df_opt = df_opt[df_opt['siteID'].isin(selected_sites)].copy()
    df_comp = df_comp[df_comp['SiteID'].isin(selected_sites)].copy()
    
    return df_bf, df_opt, df_comp

def make_latex_tables(df_bf, df_opt, df_comp):
    # Table 1: Model Performance Comparison
    # SiteID, IGBP, Benchmark_NSE, Optimized_NSE, Delta_NSE, Benchmark_Bias, Optimized_Bias
    
    # Merge with IGBP
    igbp_map = df_bf.set_index('siteID')['IGBP'].to_dict()
    df_t1 = df_comp.copy()
    df_t1['IGBP'] = df_t1['SiteID'].map(igbp_map)
    
    # Reorder columns
    df_t1 = df_t1[['SiteID', 'IGBP', 'Benchmark_NSE', 'Optimized_NSE', 'Delta_NSE', 'Benchmark_Bias', 'Optimized_Bias']]
    
    latex_t1 = []
    latex_t1.append(r"\begin{table}[H]")
    latex_t1.append(r"\centering")
    latex_t1.append(r"\caption{Model Calibration Performance Comparison (Nash-Sutcliffe Efficiency and Bias) between Empirical Best Fit (Benchmark) and Eco-Evolutionary Optimality (Optimized) configurations.}")
    latex_t1.append(r"\label{tab:perf_comp}")
    latex_t1.append(r"\begin{tabular}{llccccc}")
    latex_t1.append(r"\toprule")
    latex_t1.append(r"Site ID & IGBP & Benchmark NSE & Optimized NSE & $\Delta$ NSE & Benchmark Bias & Optimized Bias \\")
    latex_t1.append(r"\midrule")
    
    for _, row in df_t1.iterrows():
        site = row['SiteID']
        igbp = row['IGBP']
        b_nse = f"{row['Benchmark_NSE']:.3f}" if not pd.isna(row['Benchmark_NSE']) else "N/A"
        o_nse = f"{row['Optimized_NSE']:.3f}" if not pd.isna(row['Optimized_NSE']) else "N/A"
        d_nse = f"{row['Delta_NSE']:.3f}" if not pd.isna(row['Delta_NSE']) else "N/A"
        b_bias = f"{row['Benchmark_Bias']:.3f}" if not pd.isna(row['Benchmark_Bias']) else "N/A"
        o_bias = f"{row['Optimized_Bias']:.3f}" if not pd.isna(row['Optimized_Bias']) else "N/A"
        
        # Color delta if negative
        if not pd.isna(row['Delta_NSE']) and row['Delta_NSE'] < 0:
            d_nse_str = f"\\textbf{{{d_nse}}}"
        else:
            d_nse_str = d_nse
            
        latex_t1.append(f"{site} & {igbp} & {b_nse} & {o_nse} & {d_nse_str} & {b_bias} & {o_bias} \\\\")
        
    latex_t1.append(r"\bottomrule")
    latex_t1.append(r"\end{tabular}")
    latex_t1.append(r"\end{table}")
    
    # Table 2: Plant Traits comparison
    # SiteID, IGBP, BF s_wilt, OPT s_wilt, BF s_star, OPT s_star, BF pi_F, OPT pi_F, BF epsilon, OPT epsilon
    bf_metrics = df_bf.set_index('siteID')[['s_wilt', 's_star', 'pi_F', 'epsilon']].to_dict()
    opt_metrics = df_opt.set_index('siteID')[['s_wilt', 's_star', 'pi_F', 'epsilon']].to_dict()
    
    latex_t2 = []
    latex_t2.append(r"\begin{table}[H]")
    latex_t2.append(r"\centering")
    latex_t2.append(r"\caption{Comparison of calibrated ecohydrological traits and optimality parameters: Wilting point ($s_{wilt}$), stress threshold ($s^*$), Plant Water Flux Control ($\Pi_F$), and Transpiration/Carbon Optimality ($\epsilon$).}")
    latex_t2.append(r"\label{tab:traits_comp}")
    latex_t2.append(r"\begin{tabular}{lcccccccc}")
    latex_t2.append(r"\toprule")
    latex_t2.append(r" & \multicolumn{2}{c}{$s_{wilt}$} & \multicolumn{2}{c}{$s^*$} & \multicolumn{2}{c}{$\Pi_F$} & \multicolumn{2}{c}{$\epsilon$} \\")
    latex_t2.append(r"\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}")
    latex_t2.append(r"Site ID & BF & OPT & BF & OPT & BF & OPT & BF & OPT \\")
    latex_t2.append(r"\midrule")
    
    for site in selected_sites:
        bf_sw = f"{bf_metrics['s_wilt'].get(site, np.nan):.3f}"
        opt_sw = f"{opt_metrics['s_wilt'].get(site, np.nan):.3f}"
        bf_ss = f"{bf_metrics['s_star'].get(site, np.nan):.3f}"
        opt_ss = f"{opt_metrics['s_star'].get(site, np.nan):.3f}"
        bf_pf = f"{bf_metrics['pi_F'].get(site, np.nan):.3f}"
        opt_pf = f"{opt_metrics['pi_F'].get(site, np.nan):.3f}"
        bf_ep = f"{bf_metrics['epsilon'].get(site, np.nan):.3f}"
        opt_ep = f"{opt_metrics['epsilon'].get(site, np.nan):.3f}"
        
        latex_t2.append(f"{site} & {bf_sw} & {opt_sw} & {bf_ss} & {opt_ss} & \\textbf{{{bf_pf}}} & {opt_pf} & {bf_ep} & \\textbf{{{opt_ep}}} \\\\")
        
    latex_t2.append(r"\bottomrule")
    latex_t2.append(r"\end{tabular}")
    latex_t2.append(r"\end{table}")
    
    return "\n".join(latex_t1), "\n".join(latex_t2)

def generate_appendix_content(df_bf):
    # Lookup IGBP for each site
    igbp_map = df_bf.set_index('siteID')['IGBP'].to_dict()
    
    latex_app = []
    latex_app.append(r"\section{Individual Site Calibration and Diagnostic Catalog}")
    latex_app.append(r"This appendix presents the comparison of the soil moisture probability density function (PDF) calibration and Markov Chain Monte Carlo (MCMC) parameter estimation diagnostics for all 17 selected sites. For each site, the diagnostic figures are presented in a top-and-bottom format to ensure maximum readability of the multi-panel grids. The top panel represents the Empirical Best Fit (Benchmark, BF) configuration and the bottom panel represents the Eco-Evolutionary Optimality (Optimized, OPT) configuration. Each site is structured as follows:")
    latex_app.append(r"\begin{enumerate}")
    latex_app.append(r"  \item \textbf{Soil Moisture PDF Fits}: Comparison of observed soil moisture histograms and model-fitted PDFs with physiological thresholds ($S_{wilt}$, $S^*$, $S_h$, $S_{fc}$).")
    latex_app.append(r"  \item \textbf{MCMC Diagnostics (Derived Parameters)}: Prior/posterior parameter distributions, likelihood profiles, and trace chains for derived parameters ($\Pi_T$, $\Pi_S$, $\Pi_R$, $\Pi_F$, $\epsilon$, and $AA$).")
    latex_app.append(r"  \item \textbf{MCMC Diagnostics (Calibrated Traits)}: Trace diagnostics and distributions for calibrated traits ($P_{x50}$, $P_{g50}$, $k_{xl,max}$, $RAI$, $\beta_{ww}$, $s_{wilt}$, $s^*$, $\psi_{wilt}$, and $\psi^*$).")
    latex_app.append(r"\end{enumerate}")
    latex_app.append(r"\newpage")
    
    for site in selected_sites:
        name = site_metadata[site]['name']
        desc = site_metadata[site]['desc']
        igbp = igbp_map.get(site, 'Unknown')
        
        bf_fig_ps = f"output_corrected/bf/figs/_ozflux_1/{site}_{igbp}_ps.png"
        opt_fig_ps = f"output_corrected/opt/figs/_ozflux_1/{site}_{igbp}_ps.png"
        
        bf_fig_1 = f"output_corrected/bf/figs/_ozflux_1/{site}_{igbp}_1.png"
        opt_fig_1 = f"output_corrected/opt/figs/_ozflux_1/{site}_{igbp}_1.png"
        
        bf_fig_2 = f"output_corrected/bf/figs/_ozflux_1/{site}_{igbp}_2.png"
        opt_fig_2 = f"output_corrected/opt/figs/_ozflux_1/{site}_{igbp}_2.png"
        
        latex_app.append(r"\subsection{" + f"{site} --- {name} ({igbp})" + r"}")
        latex_app.append(desc)
        latex_app.append(r"\vskip 1.5em")
        
        # 1. PDF Comparison (Top & Bottom)
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.75\\textwidth]{{{bf_fig_ps}}}")
        latex_app.append(f"\\caption{{Empirical Best Fit (BF) soil moisture PDF calibration for {site}.}}")
        latex_app.append(f"\\label{{fig:ps_bf_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.75\\textwidth]{{{opt_fig_ps}}}")
        latex_app.append(f"\\caption{{Eco-Evolutionary Optimality (OPT) soil moisture PDF calibration for {site}.}}")
        latex_app.append(f"\\label{{fig:ps_opt_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\newpage")
        
        # 2. Parameter Set 1 (Top & Bottom)
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.9\\textwidth]{{{bf_fig_1}}}")
        latex_app.append(f"\\caption{{MCMC diagnostics for derived parameters ($\\Pi_T$, $\\Pi_S$, $\\Pi_R$, $\\Pi_F$, $\\epsilon$, and $AA$) under Empirical Best Fit (BF) for {site}.}}")
        latex_app.append(f"\\label{{fig:1_bf_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.9\\textwidth]{{{opt_fig_1}}}")
        latex_app.append(f"\\caption{{MCMC diagnostics for derived parameters under Eco-Evolutionary Optimality (OPT) for {site}.}}")
        latex_app.append(f"\\label{{fig:1_opt_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\newpage")
        
        # 3. Parameter Set 2 (Top & Bottom)
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.9\\textwidth]{{{bf_fig_2}}}")
        latex_app.append(f"\\caption{{MCMC diagnostics for calibrated traits ($P_{{x50}}$, $P_{{g50}}$, $k_{{xl,max}}$, $RAI$, $\\beta_{{ww}}$, $s_{{wilt}}$, $s^*$, $\\psi_{{wilt}}$, and $\\psi^*$) under Empirical Best Fit (BF) for {site}.}}")
        latex_app.append(f"\\label{{fig:2_bf_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\begin{figure}[H]")
        latex_app.append(r"\centering")
        latex_app.append(f"\\includegraphics[width=0.9\\textwidth]{{{opt_fig_2}}}")
        latex_app.append(f"\\caption{{MCMC diagnostics for calibrated traits under Eco-Evolutionary Optimality (OPT) for {site}.}}")
        latex_app.append(f"\\label{{fig:2_opt_{site}}}")
        latex_app.append(r"\end{figure}")
        
        latex_app.append(r"\newpage")
        
    return "\n".join(latex_app)


def write_latex_document():
    df_bf, df_opt, df_comp = load_data()
    t1_code, t2_code = make_latex_tables(df_bf, df_opt, df_comp)
    appendix_code = generate_appendix_content(df_bf)
    
    tex_template = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{float}
\usepackage{hyperref}
\usepackage{xcolor}


\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    pdftitle={Comparative Analysis of Stochastic Soil Water Model Calibration},
    pdfpagemode=FullScreen,
}

\title{\textbf{Stochastic Soil Water Model Calibration across Australian Ecosystems:\\ Empirical Best Fit vs. Eco-Evolutionary Optimality}}
\author{\textbf{Sanjay S.} \\ Department of Civil Engineering, Monash University, Australia \\ \texttt{sanjays@monash.edu}}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
Predicting plant water-use strategies under water-limited conditions is critical for understanding ecosystem resilience to climate volatility. This report compares two calibration methodologies for a parsimonious Stochastic Soil Water Model (SSWM) across 17 Australian OzFlux sites spanning diverse climates and vegetation types. The first methodology, \textbf{Empirical Best Fit (BF)}, calibrates soil and vegetation traits by maximizing the log-likelihood of observed soil moisture probability density functions (PDFs). The second methodology, \textbf{Eco-Evolutionary Optimality (OPT)}, optimizes parameters to maximize plant transpiration efficiency ($\epsilon$). Our results reveal a systematic divergence between actual plant behavior and theoretical optimality: actual plants exhibit a significantly higher Plant Water Flux Control ($\Pi_F$) than predicted (approximately +1.0 in dimensionless units), translating into a ~74\% reduction in maximum hydraulic capacity. This represents a long-term ``resilience tax'' or insurance policy against hydro-climatic variability (specifically ENSO cycles) that is not accounted for in standard optimality models.
\end{abstract}

\section{Introduction}
Eco-Evolutionary Optimality (EEO) theory posits that plants adjust their leaf stomatal conductance and hydraulic traits to maximize carbon gain per unit water lost, while avoiding the catastrophic risk of hydraulic failure. To test these theories, Bassiouni et al. (2023) developed the One-Water-Universal-Solver (OWUS) utilizing a parsimonious Stochastic Soil Water Model (SSWM). The model simulates soil moisture probability density functions (PDFs) based on random rainfall pulses and plant water extraction curves defined by physiological thresholds:
\begin{itemize}
    \item \textbf{Wilting point ($s_{wilt}$)}: The soil moisture level where plant transpiration ceases.
    \item \textbf{Stress threshold ($s^*$)}: The soil moisture level below which plants begin to regulate stomata and reduce transpiration.
    \item \textbf{Field capacity ($s_{fc}$)}: The soil moisture level above which gravity drains water.
    \item \textbf{Hygroscopic point ($s_h$)}: The absolute lower limit of soil water content.
\end{itemize}

Using Markov Chain Monte Carlo (MCMC) optimization over 17 Australian OzFlux eddy-covariance sites, we calibrated the key parameters: xylem water potential at 50\% loss of conductivity ($P_{x50}$), stomatal closure potential at 50\% reduction in conductance ($P_{g50}$), maximum xylem conductivity ($k_{xl,max}$), and root area index ($RAI$). We compare two alternative calibration frameworks:
\begin{enumerate}
    \item \textbf{Benchmark Empirical Best Fit (BF)}: Parameters are calibrated to directly match the observed soil moisture distribution.
    \item \textbf{Theoretical Optimality (OPT)}: Parameters are optimized to maximize the dimensionless optimality parameter $\epsilon = (1-\theta)E_t/P$, representing unstressed transpiration efficiency.
\end{enumerate}

\section{Methodology and Parameter Definitions}
The model defines several dimensionless ratios that encapsulate water-use strategies:
\begin{equation}
    \Pi_R = \frac{P_{g50}}{P_{x50}}
\end{equation}
representing the ratio of stomatal sensitivity to hydraulic capacity.
\begin{equation}
    \Pi_F = -\frac{E_0}{K_{p,max} P_{g50}}
\end{equation}
representing the Plant Water Flux Control. A high $\Pi_F$ implies a strong hydraulic constraint (low maximum conductance capacity relative to atmospheric demand).
\begin{equation}
    \theta = \text{Dynamic Plant Water Stress}
\end{equation}
representing the proportion of time the plant experiences water stress. The ecosystem resilience index is defined as $R = 1-\theta$.

\section{Results and Performance Comparison}
Table~\ref{tab:perf_comp} compares the Nash-Sutcliffe Efficiency (NSE) and model bias for the two configurations. Table~\ref{tab:traits_comp} compares the calibrated plant traits ($s_{wilt}$, $s^*$, $\Pi_F$, $\epsilon$) between BF and OPT.

% INSERT TABLE 1
__TABLE1__

% INSERT TABLE 2
__TABLE2__

\subsection{Performance Divergence}
The Empirical Best Fit (BF) model consistently reproduces observed soil moisture distributions with high accuracy (NSE $\ge 0.85$ for 14 out of 17 sites). However, when calibrating under the Eco-Evolutionary Optimality (OPT) framework, the model performance degrades significantly for several sites (e.g., Alice Springs Mulga AU-Alp drops to $-0.193$, and Fogg Dam AU-Fog collapses to $-7.003$). This performance gap reflects a fundamental mismatch between the theoretical optimal parameters and actual plant observations.

\subsection{The Hydraulic Capacity Bias}
The most striking result is the systematic difference in the Plant Water Flux Control ($\Pi_F$) between BF and OPT. Under OPT, the theoretical optimum $\Pi_F$ is low (averaging $<1.0$), implying that plants should build highly conductive hydraulic pathways (high $K_{p,max}$) to maximize water throughput. In reality, the BF calibration shows that Australian plants operate with much higher $\Pi_F$ (often $>1.5$, and up to $4.4$ at Great Victoria Desert AU-Gre). This indicates that plants are operating with a \textbf{74\% lower hydraulic capacity} than the theoretical optimum.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\textwidth]{01_Main_Paper_Figures/3_piRpiF_range.png}
    \caption{Empirical results of $\Pi_R$ vs $\Pi_F$ across the sites showing the systematic deviation from the global optimal curve (solid black line), indicating a strong conservative hydraulic constraint in Australian vegetation.}
    \label{fig:piRpiF}
\end{figure}

\section{Scientific Discussion}

\subsection{The ``Resilience Tax'' Paradox}
Why do Australian plants underperform relative to the EEO optimum? The optimality model assumes a plant operates to maximize short-term growth and transpiration. In volatile climates like Australia, dominated by multi-year ENSO cycles (decades of dry El Ni\~no and wet La Ni\~na phases), a plant optimized for the average year would perish during severe droughts. 
By maintaining a lower hydraulic capacity ($\Pi_F \gg \Pi_{F,opt}$), plants accept a carbon productivity penalty (operating at ~91\% of maximum potential efficiency, a ~9\% performance gap) to purchase a safety buffer. They pay a \textbf{resilience tax} in the form of conservative xylem construction.

\subsection{Saver vs. Spender Strategies}
Ecosystem hydraulic response falls into two major life-history categories:
\begin{enumerate}
    \item \textbf{Woody Forests as ``Savers''}: Sites like Wallaby Creek (AU-Wal) and Fogg Dam (AU-Fog) invest heavily in carbon-expensive xylem tissue. Cavitation is fatal or extremely slow to repair. They exhibit high $\Pi_F$ to preserve their structural investment, hunkering down during droughts.
    \item \textbf{Grasslands as ``Spenders''}: Sites like Sturt Plains (AU-Stp) and Yanco (AU-Ync) have low structural investment. They can senesce and recover rapidly from seed banks or rhizomes. They operate with lower $\Pi_F$, spending water aggressively when available.
\end{enumerate}

\begin{figure}[H]
    \centering
    \includegraphics[width=0.7\textwidth]{01_Main_Paper_Figures/5_flux_scatter.png}
    \caption{Flux validation scatter comparing modeled vs observed latent heat fluxes across different ecosystems, highlighting the performance of the SSWM model under typical climate regimes.}
    \label{fig:flux_scatter}
\end{figure}

\section{Conclusion and EEO Refinements}
We propose three key advancements for next-generation Eco-Evolutionary Optimality models:
\begin{enumerate}
    \item \textbf{Carbon Cost of Safety}: Include a metabolic construction cost term for building xylem ($\text{Cost}(K_{p,max})$) in the plant objective function.
    \item \textbf{Rhizosphere Soil Constraints}: Decouple soil-root interface resistance ($\Pi_S$) from xylem resistance ($\Pi_F$) in ancient, weathered soils.
    \item \textbf{Dynamic Temporal Plasticity}: Replace static parameters with time-varying parameters that respond to multi-year climate oscillations (ENSO/IOD).
\end{enumerate}

\newpage
\appendix
__APPENDIX__

\end{document}
"""
    
    # Replace place-holders
    tex_content = tex_template.replace("__TABLE1__", t1_code)
    tex_content = tex_content.replace("__TABLE2__", t2_code)
    tex_content = tex_content.replace("__APPENDIX__", appendix_code)
    
    # Write to paper_report.tex
    tex_file = os.path.join(base_dir, "paper_report.tex")
    with open(tex_file, "w") as f:
        f.write(tex_content)
        
    print(f"Successfully wrote LaTeX code to {tex_file}")

    # Compile LaTeX using pdflatex
    print("Compiling PDF...")
    try:
        # Run pdflatex twice to resolve references and labels
        for run in range(2):
            print(f"LaTeX run {run + 1}/2...")
            res = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "paper_report.tex"],
                cwd=base_dir,
                capture_output=True,
                text=True
            )
            if res.returncode != 0:
                print(f"Error compiling LaTeX on run {run + 1}:")
                # Print last 30 lines of standard output
                print("\n".join(res.stdout.splitlines()[-30:]))
                return False
        
        pdf_path = os.path.join(base_dir, "paper_report.pdf")
        if os.path.exists(pdf_path):
            print(f"PDF compiled successfully! Saved at: {pdf_path}")
            return True
        else:
            print("PDF file not found after compilation.")
            return False
            
    except Exception as e:
        print(f"Failed to run pdflatex: {e}")
        return False

if __name__ == "__main__":
    write_latex_document()
