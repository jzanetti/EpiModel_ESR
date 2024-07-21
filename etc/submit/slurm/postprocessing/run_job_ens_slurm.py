import os

from slurm.submit import submit

# Define the work directory and configuration directory
BASEDIR = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023"
# REGIONS = ["Te_Manawa_Taki", "Central", "Te_Waipounamu"]
# REGIONS = ["Auckland", "Counties_Manukau", "Northland", "Waitemata"]
REGIONS = ["Waitemata"]
EXP_IDS = {"start": 0, "end": 47, "exclude": []}
# EXP_IDS = {"start": 0, "end": 47, "exclude": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11]}
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR"
MODELS = range(1, 10)
# MODELS = range(1, 2)
PARALLEL_JOBS = None
tasks = [
    (model_id, region, exp)
    for model_id in MODELS
    for region in REGIONS
    for exp in range(EXP_IDS["start"], EXP_IDS["end"] + 1)
    if exp not in EXP_IDS["exclude"]
]

# file to store the commands in
CMDS_LIST = "slurm_commands_ens.list"

# delete it if already exists
if os.path.exists(CMDS_LIST):
    os.remove(CMDS_LIST)


# Generate the commands and write them to the file

commands = []
for proc_task in tasks:
    commands.append(
        f"python {SCRIPTDIR}/etc/scripts/run_ens.py --base_dir {BASEDIR}/{proc_task[1]}/exp_{proc_task[2]} --model_ids {proc_task[0]}"
    )

submit(
    job_name="epimodel_ens",
    job_list=commands,
    python_path=SCRIPTDIR,
    conda_env="epimodel_esr",
    total_jobs=None,
    memory_per_node=6000,
    job_priority="default",
    partition="prod",
    workdir="/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/postprocessing/slurm_jobs",
    debug=False,
)
