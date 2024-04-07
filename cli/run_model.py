import warnings
from argparse import ArgumentParser
from os import makedirs
from os.path import exists, join

from process import TOTAL_TIMESTEPS
from process.args import obtain_args
from process.model.wrapper import init_model
from process.utils import setup_logging
from process.vis import plot_grid, plot_infectiousness_profile

warnings.filterwarnings("ignore", category=UserWarning)

from logging import getLogger

logger = getLogger()


def run_epimodel_esr(
    workdir: str,
    syspop_base_path: str or None,
    syspop_diary_path: str or None,
    syspop_address_path: str or None,
    syspop_healthcare_path: str or None,
    dhb_list: list or None,
    sample_ratio: float or None,
    seed_infection: int,
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
        syspop_healthcare_path,
        dhb_list,
        sample_ratio,
        overwrite_model,
    )
    logger.info("Initial infection ...")
    model.initial_infection(seed_infection, cleanup_agents=False)

    logger.info("Running the model ...")
    for i in range(TOTAL_TIMESTEPS):
        logger.info(f" -- Step {i} ...")
        model.step(i)

    logger.info("Saving model outputs ...")
    model.postprocessing()
    model.output.to_parquet(join(workdir, "output.parquet"))

    logger.info("Plotting model outputs ...")
    plot_grid(
        workdir, model.output, state_list=[1], plot_increment=True, plot_weekly=True
    )
    plot_infectiousness_profile(workdir, model.agents)

    logger.info("Job finished")


if __name__ == "__main__":
    parser = ArgumentParser(description="Run EpiModel_ESR")
    parser = obtain_args(parser)

    args = parser.parse_args()

    """
    args = parser.parse_args(
        [
            "--workdir",
            "/tmp/test/wellington",
            "--syspop_base_path",
            "etc/test_data/wellington/syspop_base.parquet",
            "--syspop_diary_path",
            "etc/test_data/wellington/syspop_diaries.parquet",
            "--syspop_address_path",
            "etc/test_data/wellington/syspop_location.parquet",
            "--syspop_healthcare_path",
            "etc/test_data/wellington/syspop_healthcare.parquet",
            "--dhb_list",
            "Hutt_Valley",
            # "Counties Manukau",
            "--sample_ratio",
            "0.15",
            "--seed_infection",
            "20",
            "--overwrite_model",
        ]
    )
    """
    """
    args = parser.parse_args(
        [
            "--workdir",
            "/tmp/epimodel_esr_v2.0/Counties_Manukau/ens_10/",
            "--seed_infection",
            "20",
        ]
    )
    """

    run_epimodel_esr(
        args.workdir,
        args.syspop_base_path,
        args.syspop_diary_path,
        args.syspop_address_path,
        args.syspop_healthcare_path,
        [s.replace("_", " ") for s in args.dhb_list],  # e.g., counties_manukau
        float(args.sample_ratio),
        int(args.seed_infection),
        args.overwrite_model,
    )
