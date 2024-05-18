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
base_dir = "/tmp/epimodel_esr_v7.0/2022/Counties_Manukau"
obs = read_obs(
    "/home/zhangs/Github/EpiModel_ESR/etc/test_data/measles_cases_2019.parquet",
    ["Counties Manukau"],
    ref_year=2019,
)
# obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Hutt Valley"])

setup_logging(workdir=base_dir, log_type="epimodel_esr_ens_vis")

logger = getLogger()

proc_data_list = []

all_files = glob(join(base_dir, "output", "output_model_*.parquet"))
total_files = len(all_files)
for i, proc_file in enumerate(all_files):
    logger.info(f"{i}/{total_files} ...")
    proc_data = read_parquet(proc_file)
    proc_data_list.append(proc_data)

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
)

logger.info("Jobs done ...")
