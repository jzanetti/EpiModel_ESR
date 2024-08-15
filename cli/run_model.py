import warnings
from argparse import ArgumentParser

from process.args import obtain_args
from process.utils import create_dir, setup_logging
from process.wrapper import (
    create_model_wrapper,
    run_ens_wrapper,
    run_model_wrapper,
    run_vis_wrapper,
)

warnings.filterwarnings("ignore", category=UserWarning)

from logging import getLogger

logger = getLogger()


def main(
    workdir: str,
    cfg_path: str,
    model_id: str,
    create_model_flag: bool,
    run_model_flag: bool,
    run_vis_flag: bool,
    run_ens_flag: bool,
):

    create_dir(workdir)
    setup_logging(workdir=workdir)

    if create_model_flag:
        create_model_wrapper(workdir, cfg_path, model_id)

    if run_model_flag:
        run_model_wrapper(workdir, cfg_path, model_id)

    if run_vis_flag:
        run_vis_wrapper(workdir, cfg_path, model_id, plot_spread=True)

    if run_ens_flag:
        run_ens_wrapper(workdir, cfg_path)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run EpiModel_ESR")

    parser = obtain_args(parser)

    args = parser.parse_args()

    """
    args = parser.parse_args(
        [
            "--workdir",
            "/DSC/digital_twin/abm/DT_demo/v2.1/scenario2",
            "--cfg",
            # "etc/PHA_report/cfg/cfg.Counties_Manukau.yml",
            "etc/cfg/cfg.Hutt_Valley.yml",
            # "--create_model",
            "--run_model",
            "--run_vis",
            "--model_id",
            "1",
        ]
    )
    """

    main(
        args.workdir,
        args.cfg,
        args.model_id,
        args.create_model,
        args.run_model,
        args.run_vis,
        args.run_ens,
    )

    logger.info("All job done !")
