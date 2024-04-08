from glob import glob
from os.path import dirname, join

from pandas import read_parquet, to_datetime, to_numeric

from process.utils import read_obs
from process.vis import plot_grid

# base_dir = "/tmp/epimodel_esr/Auckland/ens_{run_id}"
base_dir = "/tmp/epimodel_esr_v3.0/Counties_Manukau/ens_{run_id}/"
obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Counties Manukau"])
# obs = read_obs("etc/test_data/measles_cases_2019.parquet", ["Hutt Valley"])

proc_data_list = []
for run_id in range(2):
    print(run_id)
    proc_dir = base_dir.format(run_id=run_id)
    all_files = glob(join(proc_dir, "output_ens_*.parquet"))
    for i, proc_file in enumerate(all_files):
        print(f"{run_id}: {i}")
        proc_data = read_parquet(proc_file)
        proc_data_list.append(proc_data)


plot_grid(
    dirname(proc_dir),
    proc_data_list,
    state_list=[1],
    obs=obs,
    plot_increment=True,
    plot_weekly=True,
    filename="test_ens.png",
)
