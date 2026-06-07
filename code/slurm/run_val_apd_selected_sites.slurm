#!/bin/bash
#SBATCH --job-name=val_apd_sel
#SBATCH --account=et97
#SBATCH --partition=comp
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=logs/val_apd_sel_%j.out
#SBATCH --error=logs/val_apd_sel_%j.err

module load miniforge3
conda activate ismn

cd /home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific
mkdir -p logs
mkdir -p plots_corrected_excluded_sites_v2/validation_apd_full

echo "[$(date)] Starting validation APD for selected sites..."
python -u validate_apd_tripartite_selected_sites.py
echo "[$(date)] Done."
