# OWUS Model Workflow: Explained

Here is the step-by-step breakdown of what we are doing, how the data flows, and how the "Pickle" files are created.

## 1. The Big Picture

**Objective:** We want to understand **Plant Water Use Strategies** across Australian ecosystems. Specifically, we want to know _traits_ that are hard to measure directly, such as:

- **$s_{wilt}$**: The soil moisture level where plants die/stop functioning.
- **$s^*$ (s-star)**: The moisture level where plants _start_ to feel stress and reduce transpiration.
- **$k_{max}$**: The maximum rate of water use.

Since we can't measure these everywhere, we **inverse model** them using observed Soil Moisture data.

---

## 2. Step-by-Step Workflow

### Step A: Data Preparation (Creating the Input Pickle)

- **Script:** `select_site_records.py`
- **Source:** Raw NetCDF files (`.nc`) from OzFlux towers.
- **Action:**
  1.  Reads the raw time-series: Soil Moisture (`Sws`), Rainfall (`P`), Evaporation (`Ep`).
  2.  Filters checks: specific years, no gaps, valid range (0-1).
  3.  Extracts the "Growing Season" (when plants are active).
- **Result:** Saves a **dictionary** of this clean data into a pickle file.
  - **File:** `input_data/{Site}_params.pickle`
  - **Contains:** `{'s_obs': [0.2, 0.19, ...], 'R': [0.0, 5.2, ...], 'LAI': 1.5, ...}`

### Step B: The "Model" (SSWM)

- **Script:** `sswm.py` (Stochastic Soil Water Model)
- **Logic:**
  - It is a **Probability** model.
  - It asks: _"If I have random rainfall $R$ and plants that use water at rate $E(s)$, what should the histogram (PDF) of soil moisture look like?"_
  - If parameters are wrong (e.g., predicted soil is too wet), the histogram won't match the observed data.

### Step C: The Optimization (MCMC)

- **Script:** `get_WUS_sites.py` (or `run_repair.py`)
- **Constraint:** We don't know the parameters ($s^*$, $s_{wilt}$).
- **Action (The "Job"):**
  1.  **Load:** Opens the Input Pickle (`input_data/{Site}.pickle`).
  2.  **Guess:** Picks random values for the unknown parameters.
  3.  **Run:** Runs the SSWM model to generate a _predicted_ PDF.
  4.  **Compare:** Calculates the **NSE** (Nash-Sutcliffe Efficiency) between _Predicted PDF_ vs _Observed PDF_.
  5.  **Iterate:** Uses **MCMC (Markov Chain Monte Carlo)** to intelligently try thousands of combinations until it finds the best fit.

### Step D: The Output (Creating the Output Pickle)

- **Script:** `run_mcmc.slurm` -> `get_WUS_sites.py`
- **Result:** When the best fit is found, it saves the results.
  - **File:** `output/bf/files/_ozflux_1/{Site}.pickle`
  - **Contains:**
    - **`NSE`**: How good the fit is (1.0 = perfect).
    - **`s_star`, `s_wilt`**: The discovered plant traits.
    - **`p_obs` vs `p_mod`**: The actual vs predicted histograms (used for plotting).

---

## 3. Why did it fail for some sites?

The model relies on **dynamics**.

- **Scenario:** Imagine a site is **always wet** (0.8 - 0.9 moisture).
- **The Model's Confusion:** The model tries to find the "Wilting Point" ($s_{wilt}$). But since the data _never_ dropped low, the model has absolutely no information to guess where the wilting point is. It could be 0.1, 0.5, or 0.7—the data looks the same (always 0.9).
- **Result:** The MCMC wanders aimlessly, fails to converge (`fail_eff`), or produces a mathematically impossible curve (Negative NSE).
