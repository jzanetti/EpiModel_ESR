from glob import glob
from os.path import join

from pandas import read_parquet

from process.utils import read_obs
from process.vis.wrapper import plot_wrapper

# base_dir = "/tmp/epimodel_esr/Auckland/ens_{run_id}"
# base_dir = "/tmp/epimodel_esr_v3.0/Counties_Manukau/ens_{run_id}/"
# obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Counties Manukau"])
base_dir = "/tmp/epimodel_esr_v5.0/Northland"
obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Northland"], ref_year=2024)
# obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Hutt Valley"])

proc_data_list = []

all_files = glob(join(base_dir, "output_model_*.parquet"))
total_files = len(all_files)
for i, proc_file in enumerate(all_files):
    print(f"{i}/{total_files}")
    proc_data = read_parquet(proc_file)
    proc_data_list.append(proc_data)
    if i > 15:
        break

plot_wrapper(
    base_dir,
    proc_data_list,
    plot_weekly_data=True,
    plot_percentile_flag=True,
    obs=obs,
    filename=f"infection_all",
)
