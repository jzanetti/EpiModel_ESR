from copy import deepcopy
from datetime import datetime
from logging import getLogger
from os.path import join

from pandas import read_parquet as pandas_read_parquet

from process import ENS_NUMBER, SAVED_MODEL_PATH, TOTAL_TIMESTEPS
from process.model.wrapper import Epimodel_esr
from process.utils import open_saved_model, read_cfg, read_obs, read_syspop_data
from process.vis.wrapper import plot_wrapper

logger = getLogger()


def create_model_wrapper(workdir: str, cfg_path: str, model_id: str):
    cfg = read_cfg(cfg_path, task_name="create_model")

    saved_model_path = SAVED_MODEL_PATH.format(workdir=workdir, id=model_id)

    data = read_syspop_data(
        cfg["data_path"]["syspop_base"],
        cfg["data_path"]["syspop_diary"],
        cfg["data_path"]["syspop_address"],
        cfg["data_path"]["syspop_healthcare"],
        cfg["data_path"]["obs"],
        sample_p=cfg["sample_ratio"],
        dhb_list=cfg["dhb_list"],
        sample_all_hhd_flag=True,
    )
    model = Epimodel_esr(data)
    model.save(saved_model_path)


def run_model_wrapper(workdir: str, cfg_path: str, model_id: str):
    """Run epimodel_ESR

    Args:
        workdir (str): Working directory
        model_id (str): Model ID
        cfg_path (str): Configure file path
    """

    cfg = read_cfg(cfg_path, task_name="run_model")

    seed_infection = cfg["seed_infection"]
    intital_timestep = datetime.strptime(str(cfg["intital_timestep"]), "%Y%m%d")

    model = open_saved_model(SAVED_MODEL_PATH.format(workdir=workdir, id=model_id))

    for ens_i in range(ENS_NUMBER):
        logger.info(f"Initialize the EpiModel_ESR {ens_i}...")
        proc_model = deepcopy(model)
        proc_model.initial_infection(
            seed_infection, intital_timestep, cleanup_agents=True
        )
        logger.info(f"Running the model {ens_i} ...")
        for i in range(TOTAL_TIMESTEPS):
            logger.info(f" -- Step {i} ...")
            proc_model.step(i)

        logger.info(f"Saving model outputs {ens_i} ...")
        proc_model.postprocessing(intital_timestep)
        proc_model.output.to_parquet(
            join(workdir, f"output_model_{model_id}_ens_{ens_i}.parquet")
        )

    logger.info("Simulation finished")


def run_vis_wrapper(workdir: str, cfg_path: str, model_id: str):
    """Run model visualization

    Args:
        workdir (str): Working directory
        model_id (str): Model ID
    """
    cfg = read_cfg(cfg_path, task_name="run_vis")

    obs_path = cfg["data_path"]["obs"]
    dhb_list = cfg["dhb_list"]

    all_model_outputs = []

    for ens_i in range(ENS_NUMBER):
        proc_model = pandas_read_parquet(
            join(workdir, f"output_model_{model_id}_ens_{ens_i}.parquet")
        )
        all_model_outputs.append(proc_model)

    if obs_path is not None:
        obs = read_obs(obs_path, dhb_list, ref_year=2024)

    plot_wrapper(
        workdir,
        all_model_outputs,
        plot_weekly_data=True,
        obs=obs,
        filename=f"infection_{model_id}",
    )

    logger.info("Visualization finished")
