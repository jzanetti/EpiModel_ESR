import warnings
from argparse import ArgumentParser
from os import makedirs
from os.path import exists, join

from process import SAVED_MODEL_PATH, TOTAL_TIMESTEPS
from process.args import obtain_args
from process.model.wrapper import Epimodel_esr
from process.utils import open_saved_model, read_syspop_data, setup_logging
from process.vis import plot_grid, plot_infectiousness_profile

warnings.filterwarnings("ignore", category=UserWarning)

from logging import getLogger

logger = getLogger()


def init_model(
    workdir: str,
    syspop_base_path: str or None,
    syspop_diary_path: str or None,
    syspop_address_path: str or None,
    dhb_list: list or None,
    sample_ratio: float or None,
    overwrite_model: bool,
):
    """Initialize the model

    Args:
        workdir (str): Working directory
        syspop_base_path (strorNone): Synthetic population (base) data path
        syspop_diary_path (strorNone): Synthetic population (diary) data path
        syspop_address_path (strorNone): Synthetic population (address) data path
        dhb_list (listorNone): DHB list to be selected from
        sample_ratio (floatorNone): Interaction sample percentage
        overwrite_model (bool): If previous model is presented, we will rewrite it

    Returns:
        _type_: _description_
    """
    saved_model_path = SAVED_MODEL_PATH.format(workdir=workdir)

    if not exists(saved_model_path) or overwrite_model:
        data = read_syspop_data(
            syspop_base_path,
            syspop_diary_path,
            syspop_address_path,
            sample_p=sample_ratio,
            dhb_list=dhb_list,
        )
        model = Epimodel_esr(data, initial_n=50)
        model.save(saved_model_path)
    else:
        model = open_saved_model(saved_model_path)

    return model


def run_epimodel_esr(
    workdir: str,
    syspop_base_path: str or None,
    syspop_diary_path: str or None,
    syspop_address_path: str or None,
    dhb_list: list or None,
    sample_ratio: float or None,
    overwrite_model: bool,
):
    """Run epimodel_ESR

    Args:
        workdir (str): Working directory
        syspop_base_path (strorNone): Synthetic population (base) data path
        syspop_diary_path (strorNone): Synthetic population (diary) data path
        syspop_address_path (strorNone): Synthetic population (address) data path
        dhb_list (listorNone): DHB list to be selected from
        sample_ratio (floatorNone): Interaction sample percentage
        overwrite_model (bool): If previous model is presented, we will rewrite it
    """
    if not exists(workdir):
        makedirs(workdir)

    setup_logging(workdir=workdir)

    logger.info("Initialize the EpiModel_ESR ...")
    model = init_model(
        workdir,
        syspop_base_path,
        syspop_diary_path,
        syspop_address_path,
        dhb_list,
        sample_ratio,
        overwrite_model,
    )

    logger.info("Running the model ...")
    for i in range(TOTAL_TIMESTEPS):
        model.step(i)

    logger.info("Saving model outputs ...")
    agent_state = model.datacollector.get_agent_vars_dataframe()
    agent_state.reset_index(inplace=True)

    agent_state.to_parquet(join(workdir, "output.parquet"))

    logger.info("Plotting model outputs ...")
    plot_grid(workdir, agent_state, state_list=[1, 2, 3])
    plot_infectiousness_profile(workdir, model.agents)

    logger.info("Job finished")


if __name__ == "__main__":
    parser = ArgumentParser(description="Creating NZ data")
    parser = obtain_args(parser)

    # args = parser.parse_args()

    args = parser.parse_args(
        [
            "--workdir",
            "/tmp/test",
            "--syspop_base_path",
            "/tmp/syspop_test/Auckland/syspop_base.parquet",
            "--syspop_diary_path",
            "/tmp/syspop_test/Auckland/syspop_diaries.parquet",
            "--syspop_address_path",
            "/tmp/syspop_test/Auckland/syspop_location.parquet",
            "--dhb_list",
            "Counties Manukau",
            "--sample_ratio",
            "0.001",
        ]
    )

    run_epimodel_esr(
        args.workdir,
        args.syspop_base_path,
        args.syspop_diary_path,
        args.syspop_address_path,
        [s.replace("_", " ") for s in args.dhb_list],  # e.g., counties_manukau
        float(args.sample_ratio),
        args.overwrite_model,
    )
