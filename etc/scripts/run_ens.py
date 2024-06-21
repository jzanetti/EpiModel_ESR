from argparse import ArgumentParser
from glob import glob
from logging import getLogger
from os.path import join

from pandas import read_parquet

from process.utils import read_obs, setup_logging
from process.vis.wrapper import plot_wrapper

# nohup python etc/scripts/run_ens.py >& log &

# base_dir = "/tmp/epimodel_esr/Auckland/ens_{run_id}"
# base_dir = "/tmp/epimodel_esr_v3.0/Counties_Manukau/ens_{run_id}/"
# obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Counties Manukau"])
# base_dir = "/DSC/digital_twin/abm/PHA_report_202405/data/2023/Counties_Manukau"


def main(
    base_dir: str,
    obs_path: str or None = None,
    obs_ref_year: int = 2019,
    obs_loc_list: list = ["Counties Manukau"],
):
    """_summary_

    Args:
        base_dir (str): Base directory, e.g.,/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023/Te_Manawa_Taki/exp_5
        obs_path (str, optional): Observation path. Defaults to "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet".
        obs_ref_year (int, optional): Observation year. Defaults to 2019.
    """
    # base_dir = "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023/Te_Manawa_Taki/exp_5"

    obs = None
    if obs_path is not None:
        obs = read_obs(
            "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet",
            obs_loc_list,
            ref_year=obs_ref_year,
        )
    # obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Hutt Valley"])
    obs = None
    setup_logging(workdir=base_dir, log_type="epimodel_esr_ens_vis")

    logger = getLogger()

    proc_data_list = []

    all_files = glob(join(base_dir, "output", "output_model_*.parquet"))
    total_files = len(all_files)
    for i, proc_file in enumerate(all_files):
        logger.info(f"{i}/{total_files} ...")
        proc_data = read_parquet(proc_file)
        proc_data_list.append(proc_data)

    logger.info("Plotting ...")
    plot_wrapper(
        join(base_dir, "vis"),
        proc_data_list,
        plot_weekly_data=True,
        plot_percentile_flag=True,
        obs=obs,
        xlabel_str="Date",
        ylabel_str="Number of cases",
        title_str="Number of simulated and confirmed cases",
        filename=f"infection_all",
        remove_outlier=False,
        # ylim_range=[0, 250],
    )

    logger.info("Jobs done ...")


if __name__ == "__main__":
    parser = ArgumentParser(description="Run EpiModel_ESR")

    parser.add_argument(
        "--base_dir",
        type=str,
        required=True,
        help="Base working directory",
    )

    parser.add_argument(
        "--obs_path",
        type=str,
        required=False,
        default=None,
        # "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet",
        help="Observation",
    )

    parser.add_argument(
        "--obs_ref_year",
        type=int,
        required=False,
        default=2019,
        help="Observation reference year",
    )

    parser.add_argument(
        "--obs_loc_list",
        nargs="+",
        help="Observation locations",
        default="'Counties Manukau'",
        required=False,
    )

    args = parser.parse_args(
        # [
        #    "--base_dir",
        #    "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023/Te_Manawa_Taki/exp_5",
        # ]
    )

    main(args.base_dir, args.obs_path, args.obs_ref_year, args.obs_loc_list)
