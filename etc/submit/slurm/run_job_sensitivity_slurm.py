import os
import subprocess

os.chdir("/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm")

# Define the work directory and configuration directory
CFGDIR = "/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/cfg/sensitivity_runs"
WORKDIR = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023"
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR"

EXPS_NUM = (
    47  # each exp contains different model (sensitivity) configurations, total 47
)
MODELS_NUM = 10  # Each model contains different scenarios of social dynamics, total 10

# Central: kscprod-data3(started)
# Te_Manawa_Taki: kscprod-data1 (started)
REGION_NAMES = ["Central", "Te_Manawa_Taki", "Te_Waipounamu"]

# file to store the commands in
CMDS_LIST = "slurm_commands.list"

# delete it if already exists
if os.path.exists(CMDS_LIST):
    os.remove(CMDS_LIST)


tasks = [
    (region, exp, model)
    for region in REGION_NAMES
    for exp in range(EXPS_NUM + 1)
    for model in range(1, MODELS_NUM + 1)
]

# Generate the commands and write them to the file
with open(CMDS_LIST, "w") as file:
    for region_name in REGION_NAMES:
        for exp_num in range(EXPS_NUM + 1):
            for model_id in range(1, MODELS_NUM + 1):
                cfg_path = f"{CFGDIR}/cfg.{region_name}.{exp_num}.yml"
                workdir_base = f"{WORKDIR}/{region_name}"
                command = f"python {SCRIPTDIR}/cli/run_model.py --run_model --run_vis --workdir {workdir_base}/exp_{exp_num} --cfg {cfg_path} --model_id {model_id}"
                file.write(command + "\n")

# Get the number of commands
NUM_CMDS = sum(1 for line in open(CMDS_LIST))

# Submit the job array to the scheduler
subprocess.run(
    [
        "sbatch",
        "--array=1-" + str(NUM_CMDS),
        "--export=ALL,CMDS_LIST=" + CMDS_LIST,
        "arrayjob.sl",
    ]
)
