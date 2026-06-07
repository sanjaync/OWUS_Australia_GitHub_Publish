#!/bin/bash
#SBATCH --job-name=figs_selected
#SBATCH --account=et97
#SBATCH --partition=comp
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=logs/figs_selected_%j.out
#SBATCH --error=logs/figs_selected_%j.err

module load miniforge3
conda activate ismn

cd /home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_3_scientific
mkdir -p logs
mkdir -p plots_corrected_excluded_sites_v2/paper_figures

echo "[$(date)] Starting figure generation for selected sites..."
python -u run_paper_figs_selected_sites.py
echo "[$(date)] Done."
