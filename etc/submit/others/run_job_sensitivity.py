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
WORKDIR = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023"
CFGDIR = "/home/zhangs/Github/EpiModel_ESR/etc/PHA_report/cfg/sensitivity_runs"
SCRIPTDIR = "/home/zhangs/Github/EpiModel_ESR"

MODELS_NUM = 10  # Each model contains different scenarios of social dynamics
EXPS_NUM = 47  # each exp contains different model (sensitivity) configurations

# Central: kscprod-data3(started)
# Te_Manawa_Taki: kscprod-data1 (started)
REGION_NAMES = ["Te_Manawa_Taki"]

CREATE_MODEL = False  # DO NOT SWITCH THIS ON UNLESS NECESSARY
RUN_MODEL = True
CONCURRENT_JOBS = 30


# Function to run the model creation or execution
def run_model(region_name, exp_num, model_id):
    cfg_path = f"{CFGDIR}/cfg.{region_name}.{exp_num}.yml"
    workdir_base = f"{WORKDIR}/{region_name}"
    os.makedirs(workdir_base, exist_ok=True)

    if CREATE_MODEL:
        logger.info(
            f"Running iteration (create_model) {region_name}, {exp_num}, {model_id}"
        )
        command = (
            f"source activate epimodel_esr "
            + f"&& PYTHONPATH={SCRIPTDIR} python cli/run_model.py --create_model --workdir {workdir_base} --cfg {cfg_path} --model_id {model_id} "
            + f">& {workdir_base}/log.create_model_{exp_num}_{model_id} &"
        )
        logger.info(command)
        subprocess.run(command, shell=True, check=True, cwd=SCRIPTDIR)

    if RUN_MODEL:
        logger.info(
            f"Running iteration (run_model) {region_name}, {exp_num}, {model_id}"
        )
        command = (
            f"source activate epimodel_esr "
            + f"&& PYTHONPATH={SCRIPTDIR} python cli/run_model.py --run_model --run_vis --workdir {workdir_base}/exp_{exp_num} --cfg {cfg_path} --model_id {model_id} "
            + f">& {workdir_base}/log.run_model_{exp_num}_{model_id} &"
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
    (region, exp, model)
    for region in REGION_NAMES
    for exp in range(EXPS_NUM + 1)
    for model in range(1, MODELS_NUM + 1)
]

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
