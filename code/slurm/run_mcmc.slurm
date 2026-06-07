#!/bin/bash
#SBATCH --job-name=owus_mcmc
#SBATCH --account=et97
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --partition=comp
#SBATCH --output=mcmc_slurm_%j.log
#SBATCH --error=mcmc_slurm_%j.err
#SBATCH --mail-user=sanjaync@monash.edu
#SBATCH --mail-type=BEGIN,END,FAIL

# OWUS MCMC Optimization Job
# Runs get_WUS_sites.py with proper environment

# Load environment
module load miniforge3
conda activate ismn

# Set working directory
cd /home/sanjays/et97_scratch2/oldscratch/Ozflux_data_full/OWUS_australia_agent_2

# Run MCMC optimization
echo "Starting MCMC at $(date)"
echo "Running on host: $(hostname)"
echo "Number of CPUs: $SLURM_CPUS_PER_TASK"

python get_WUS_sites.py

echo "MCMC completed at $(date)"
