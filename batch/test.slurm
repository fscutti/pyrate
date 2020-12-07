#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --time=0-12:00:00
#SBATCH --partition=physical

# Load required modules
#module purge
#source /usr/local/module/spartan_old.sh
#module load Python/3.5.2-goolf-2015a

# Launch multiple process python code
echo "Searching for mentions"
time srun -n 8 pyrate -j ../scripts/job_WC.yaml

