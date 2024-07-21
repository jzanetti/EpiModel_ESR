import os

from slurm.submit import submit

os.chdir("/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm")

# Define the work directory and configuration directory
CFGDIR = "/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/cfg/sensitivity_runs"
WORKDIR = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023"
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR"

PARALLEL_JOBS = None
EXPS_NUM = 47  # 47

# Each model contains different scenarios of social dynamics, total 10
MODELS_NUM = 10


# REGION_NAMES = ["Central", "Te_Manawa_Taki", "Te_Waipounamu"]
# REGION_NAMES = ["Northern"]
REGION_NAMES = ["Auckland", "Counties_Manukau", "Waitemata", "Northland"]


tasks = [
    (region, exp, model)
    for region in REGION_NAMES
    for exp in range(EXPS_NUM + 1)
    for model in range(1, MODELS_NUM + 1)
]

cmd_lists = []
for region_name in REGION_NAMES:
    for exp_num in range(0, EXPS_NUM + 1):
        for model_id in range(1, MODELS_NUM + 1):
            cfg_path = f"{CFGDIR}/cfg.{region_name}.{exp_num}.yml"
            workdir_base = f"{WORKDIR}/{region_name}"
            cmd = f"python {SCRIPTDIR}/cli/run_model.py --run_model --run_vis --workdir {workdir_base}/exp_{exp_num} --cfg {cfg_path} --model_id {model_id}"
            cmd_lists.append(cmd)


submit(
    job_name="epimodel_northern",
    job_list=cmd_lists,
    python_path=SCRIPTDIR,
    conda_env="epimodel_esr",
    total_jobs=PARALLEL_JOBS,
    memory_per_node=8000,
    job_priority="default",
    partition="prod",
    workdir="/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/models/slurm_job2",
    debug=False,
)
