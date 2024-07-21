from argparse import ArgumentParser, BooleanOptionalAction
from glob import glob
from logging import getLogger
from os.path import basename, join

from dask.dataframe import read_parquet as dask_read_parquet
from pandas import read_parquet

from process.utils import read_obs, setup_logging
from process.vis.wrapper import plot_wrapper


def main(
    base_dir: str,
    obs_path: str or None = None,
    obs_ref_year: int = 2019,
    obs_loc_list: list = ["Counties Manukau"],
    only_group_data: bool = False,
    model_ids: list or None = None,
    use_dask: bool = True,
):
    """_summary_

    Args:
        base_dir (str): Base directory,
            e.g.,/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023/Te_Manawa_Taki/exp_5
        obs_path (str, optional): Observation path.
            Defaults to "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet".
        obs_ref_year (int, optional): Observation year. Defaults to 2019.
    """
    logger = setup_logging(workdir=base_dir, log_type="epimodel_esr_ens_vis")
    logger.info(base_dir)

    obs = None
    if obs_path is not None:
        obs = read_obs(
            "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet",
            obs_loc_list,
            ref_year=obs_ref_year,
        )
    # obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Hutt Valley"])
    obs = None
    proc_data_list = []

    if model_ids is None:
        all_files1 = glob(join(base_dir, "output_pp", "output_model_*.parquet"))
    else:
        all_files1 = []
        for proc_model_id in model_ids:
            all_files1.extend(
                glob(
                    join(
                        base_dir, "output_pp", f"output_model_{proc_model_id}_*.parquet"
                    )
                )
            )

    all_filesname1 = []
    for proc_file in all_files1:
        all_filesname1.append(basename(proc_file))

    all_filesname1 = []
    if model_ids is None:
        all_files2 = glob(join(base_dir, "output", "output_model_*.parquet"))
    else:
        all_files2 = []
        for proc_model_id in model_ids:
            all_files2.extend(
                glob(
                    join(base_dir, "output", f"output_model_{proc_model_id}_*.parquet")
                )
            )

    all_filesname2 = []
    for proc_file in all_files2:
        all_filesname2.append(basename(proc_file))

    all_filename = list(set(all_filesname1 + all_filesname2))

    all_files = []

    for proc_filename in all_filename:
        if proc_filename in all_filesname1:
            all_files.append(join(base_dir, "output_pp", proc_filename))
        else:
            all_files.append(join(base_dir, "output", proc_filename))

    total_files = len(all_files)

    for i, proc_file in enumerate(all_files):
        logger.info(f"{i}/{total_files} ...")
        if use_dask:
            proc_data = dask_read_parquet(
                proc_file, columns=["Step", "State_new_2"], blocksize="10MB"
            )
        else:
            proc_data = read_parquet(proc_file)[["Step", "State_new_2"]]
        proc_data["State_new_2"] = proc_data["State_new_2"].astype("int8")
        # proc_data = proc_data.compute()
        proc_data_list.append(proc_data)

    if len(proc_data_list) == 0:
        return

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
        model_ids=model_ids,
        only_group_data=only_group_data,
        use_dask=use_dask,
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

    parser.add_argument("--only_group_data", action=BooleanOptionalAction)

    parser.add_argument(
        "--model_ids",
        nargs="+",
        help="Model IDs",
        default=None,
        required=False,
    )

    args = parser.parse_args(
        #    [
        #        "--base_dir",
        #        "/DSC/digital_twin/abm/PHA_report_202405/sensitivity/data/2023/Waitemata/exp_0",
        #        "--model_ids",
        #        "1",
        #    ]
    )

    main(
        args.base_dir,
        args.obs_path,
        args.obs_ref_year,
        args.obs_loc_list,
        args.only_group_data,
        args.model_ids,
    )
