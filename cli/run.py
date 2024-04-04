import warnings
from argparse import ArgumentParser
from os import makedirs
from os.path import exists, join

from process.model.wrapper import Epimodel_esr
from process.utils import read_syspop_data, setup_logging
from process.vis import plot_grid

warnings.filterwarnings("ignore", category=UserWarning)

from logging import getLogger

logger = getLogger()


def run_model(
    workdir: str,
    syspop_base_path: str,
    syspop_diary_path: str,
    syspop_address_path: str,
    dhb_list: list or None,
    sample_ratio: float,
):

    if not exists(workdir):
        makedirs(workdir)

    setup_logging(workdir=workdir)

    data = read_syspop_data(
        syspop_base_path,
        syspop_diary_path,
        syspop_address_path,
        sample_p=sample_ratio,
        dhb_list=dhb_list,
    )

    model = Epimodel_esr(data, initial_n=50)

    for i in range(180):
        model.step(i)

    agent_state = model.datacollector.get_agent_vars_dataframe()
    agent_state.reset_index(inplace=True)

    agent_state.to_parquet(join(workdir, "output.parquet"))

    logger.info("job finished")

    # print("plot ...")
    # plot_grid(agent_state, state_list=[1, 2, 3])


if __name__ == "__main__":
    parser = ArgumentParser(description="Creating NZ data")

    parser.add_argument(
        "--workdir",
        type=str,
        required=False,
        default="/tmp/epimodel_esr",
        help="Working directory",
    )

    # syspop_base_path: str, syspop_diary_path: str, syspop_address_path: str
    parser.add_argument(
        "--syspop_base_path",
        type=str,
        required=True,
        help="Synthetic population (base) data path",
    )

    parser.add_argument(
        "--syspop_diary_path",
        type=str,
        required=False,
        help="Synthetic population (diary) data path",
    )

    parser.add_argument(
        "--syspop_address_path",
        type=str,
        required=False,
        help="Synthetic population (address) data path",
    )
    parser.add_argument(
        "--dhb_list",
        nargs="+",
        help="New Zealand DHB list",
        required=False,
        default=None,
    )

    parser.add_argument(
        "--sample_ratio",
        type=float,
        help="The percentage of interactions to be used",
        required=False,
        default=0.1,
    )
    args = parser.parse_args()

    """
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
        ]
    )
    """

    run_model(
        args.workdir,
        args.syspop_base_path,
        args.syspop_diary_path,
        args.syspop_address_path,
        [s.replace("_", " ") for s in args.dhb_list],  # e.g., counties_manukau
        float(args.sample_ratio),
    )
