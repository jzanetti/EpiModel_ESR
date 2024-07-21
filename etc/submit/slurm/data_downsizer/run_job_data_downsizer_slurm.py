import os
import subprocess

os.chdir("/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/data_downsizer")
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/scripts"
regions = [
    "Auckland",
    "Central",
    "Counties_Manukau",
    "Northland",
    "Te_Manawa_Taki",
    "Te_Waipounamu",
    "Waitemata",
]


# Generate the commands and write them to the file
commands = []
for proc_task in regions:
    for exp_start in range(0, 48, 2):
        exp_end = exp_start + 1
        commands.append(
            f"python {SCRIPTDIR}/data_downsizer.py --region {proc_task} --exp_start {exp_start} --exp_end {exp_end}"
        )


from slurm.submit import submit

submit(
    job_name="data_downsizer",
    job_list=commands,
    python_path=SCRIPTDIR,
    conda_env="epimodel_esr",
    total_jobs=None,
    memory_per_node=8000,
    job_priority="default",
    partition="prod",
    workdir="/home/zhangs/Github/EpiModel_ESR/etc/submit/slurm/data_downsizer/slurm_jobs2",
    debug=False,
)
