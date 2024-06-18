#!/bin/bash
#SBATCH --job-name epimodel_esr
#SBATCH --partition prod
#SBATCH --output /home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/log/epimodel_esr.%A.%a.out # STDOUT
#SBATCH --error /home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/log/epimodel_esr.%A.%a.log # STDERR

SCRIPTDIR=/home/zhangs/Github/EpiModel_ESR

source activate epimodel_esr
export PYTHONPATH=${SCRIPTDIR} 

COMMAND=`sed "${SLURM_ARRAY_TASK_ID}q;d" ${CMDS_LIST}`

echo $COMMAND
eval $COMMAND