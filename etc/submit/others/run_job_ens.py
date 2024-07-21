import concurrent.futures
import logging
import os
import subprocess

# Configure the logging module
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Now you can use logging.info instead of print
logger = logging.getLogger()


# Define the work directory and configuration directory
BASEDIR = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023"
REGIONS = ["Te_Manawa_Taki"]
EXP_IDS = {"start": 0, "end": 14, "exclude": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11]}
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR"

CONCURRENT_JOBS = 3


# Function to run the model creation or execution
def run_model(region_name, exp_id):

    logger.info(f"Running iteration (create_model) {region_name}, {exp_id}")
    command = (
        f"export PYTHONPATH={SCRIPTDIR} "
        + f"&& ~/miniconda3/envs/epimodel_esr/bin/python /home/zhangs/Github/EpiModel_ESR/etc/scripts/run_ens.py --base_dir {BASEDIR}/{region_name}/exp_{exp_id}"
    )
    logger.info(command)
    result = subprocess.run(
        command,
        shell=True,
        check=True,
        cwd=SCRIPTDIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    logger.info(result.stdout)
    logger.info(result.stderr)


# Create a list of all tasks to be run
tasks = [
    (region, exp)
    for region in REGIONS
    for exp in range(EXP_IDS["start"], EXP_IDS["end"] + 1)
    if exp not in EXP_IDS["exclude"]
]

logger.info(f"Total jobs {len(tasks)} ...")

# Run the tasks with 10 workers (concurrent runs)
with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_JOBS) as executor:
    # Submit all tasks to the executor
    future_to_task = {executor.submit(run_model, *task): task for task in tasks}

    # Wait for all tasks to complete
    for future in concurrent.futures.as_completed(future_to_task):
        task = future_to_task[future]
        try:
            # Get the result of the task (will raise exceptions if any occurred)
            future.result()
        except Exception as exc:
            logger.info(f"Task {task} generated an exception: {exc}")

logger.info("All tasks completed.")
