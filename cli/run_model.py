import warnings
from argparse import ArgumentParser
from os import makedirs
from os.path import exists

from process.args import obtain_args
from process.utils import setup_logging
from process.wrapper import create_model_wrapper, run_model_wrapper, run_vis_wrapper

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
):

    if not exists(workdir):
        makedirs(workdir)
    setup_logging(workdir=workdir)

    if create_model_flag:
        create_model_wrapper(workdir, cfg_path, model_id)

    if run_model_flag:
        run_model_wrapper(workdir, cfg_path, model_id)

    if run_vis_flag:
        run_vis_wrapper(workdir, cfg_path, model_id)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run EpiModel_ESR")

    parser = obtain_args(parser)

    args = parser.parse_args()

    """
    args = parser.parse_args(
        [
            "--workdir",
            "/tmp/epimodel_esr_v7.0/Counties_Manukau",
            "--cfg",
            "etc/PHA_report/cfg/cfg.Counties_Manukau.yml",
            "--create_model",
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
    )
