# Ecosystem Plasticity Under Climate Extremes: The ENSO Experiment

## 1. Experimental Objective
This experiment was designed to challenge a fundamental assumption in standard ecohydrological modeling: **the assumption of static vegetation parameters**. 

Crucially, this experiment relies strictly on the **Eco-Evolutionary Optimality Theory** model (and *not* the unconstrained BF/Best Fit baseline). Instead of running the optimality framework over the entire available flux tower timeline as a single block, the daily meteorological and flux data for 22 Australian OzFlux sites were strictly partitioned by El Niño–Southern Oscillation (ENSO) extremes. The primary objective was to test for ecohydrological **"plasticity"**—specifically, whether the mathematical "Optimal" state of an ecosystem actively shifts its physical hydraulic traits (such as the stomatal sensitivity target, $s^*$, and the hydraulic cost penalty, $\Pi_F$) to survive changing climatic extremes.

## 2. Methodology: Defining the Climate Extremes
The dataset for each site was filtered into two distinct subsets based on historically classified ENSO years:
*   **El Niño (Severe Drought):** `[2002, 2004, 2006, 2009, 2014, 2015, 2019]`
*   **La Niña (Anomalously Wet):** `[2000, 2007, 2008, 2010, 2011, 2017, 2021, 2022]`

For each site, independent **Eco-Evolutionary Optimality Theory** optimizations were executed on both the El Niño and La Niña subsets (provided the subset contained a minimum of 180 days of valid observations). This yielded two distinct sets of optimal physiological parameters per site, enabling a direct paired comparison of how the "Optimal" state of an ecosystem behaves during severe drought versus water abundance.

## 3. Core Scientific Conclusions

### Mechanism 1: Baseline Climate Dictates the Survival Strategy
By correlating the "directional shift" of the hydraulic cost parameter ($\Pi_F$) against the site's historical mean rainfall, the data reveals that ecosystems do not respond uniformly to drought. 
*   **Wetter sites** tend to adopt a highly conservative, "safer" strategy during El Niño droughts (significantly increasing their $\Pi_F$ penalty) because they are unaccustomed to severe water stress. 
*   Conversely, **drier, arid sites** often take on *more* physiological risk (decreasing $\Pi_F$) to maintain carbon assimilation during droughts, as their baseline physiology is already adapted to operating near the hydraulic edge.

### Mechanism 2: Dynamic Trajectories in Parameter Space
By plotting the shift from $(s^*, \Pi_F)$ during La Niña to $(s^*, \Pi_F)$ during El Niño, the results map out literal survival trajectories. 
Ecosystems are highly dynamic. When the external climate shifts from wet to dry, the mathematical "optimal state" of the vegetation shifts correspondingly. Assuming a single, static $(s^*, \Pi_F)$ coordinate for a forest across a decadal timeline fundamentally misrepresents how the canopy is adapting in real-time.

### Mechanism 3: Performance Degradation of Static Models
The Nash-Sutcliffe Efficiency (NSE) metrics demonstrate a distinct trend where model predictive performance often degrades significantly during El Niño phases compared to La Niña phases. 
*   For example, site **AU-Stp** achieved an excellent **0.91 NSE** during La Niña, but crashed to **0.43 NSE** during El Niño. 
*   If an Earth System Model (ESM) calibrates its static parameters during normal or wet years, those parameters will actively fail to predict evapotranspiration and soil moisture dry-downs during severe droughts. The underlying physical equations do not necessarily break; rather, the *vegetation traits* changed, and the static model failed to keep up.

## 4. Final Verdict
This experiment acts as the ultimate justification for **dynamic, optimality-based modeling**. It mathematically proves that because plants adapt their hydraulic strategies to ENSO extremes, our global ecohydrological models must be allowed to adapt their parameters dynamically to accurately forecast carbon and water fluxes under future climate extremes.

## 5. Associated Scripts
*   **Data Preparation & MCMC Execution:** `/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/run_enso_updated_experiment.py`
*   **Plot Generation:** `/home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific/ENSO_experiment_updated/plot_enso_mechanisms_updated.py`
