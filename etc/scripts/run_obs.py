import matplotlib.pyplot as plt

from process.utils import read_obs

obs_path = "etc/test_data/measles_cases_2019.parquet"
dhb_list = ["Northland"]

obs = read_obs(obs_path, dhb_list)

obs["daily"].plot()
plt.savefig("obs.png")
plt.close()
