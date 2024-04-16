from os.path import join
from random import sample as random_sample

from matplotlib.cm import ScalarMappable, viridis
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.pyplot import (
    close,
    figure,
    fill_between,
    grid,
    legend,
    plot,
    savefig,
    subplots,
    tight_layout,
    title,
    xlabel,
    xticks,
    ylabel,
)
from mesa.agent import AgentSet as mesa_agentset
from numpy import arange, array, linspace, percentile
from pandas import DataFrame

from process import VIS_COLOR
from process.model.disease import State
from process.utils import daily2weekly_data


def plot_infectiousness_profile(
    workdir: str, model_agents: mesa_agentset, sample_size: int = 100
):
    total_agents = len(model_agents)

    agents_ids = random_sample(list(range(total_agents)), sample_size)

    for proc_agent_id in agents_ids:
        proc_infectiousness_profile = model_agents[proc_agent_id].infectiousness_profile
        plot(
            list(proc_infectiousness_profile.keys()),
            list(proc_infectiousness_profile.values()),
            linestyle="-",
            color="k",
        )
    xlabel("Step (days)")
    ylabel("Infectiousness")
    title("Infectiousness profile")
    grid(True)
    legend()
    tight_layout()
    savefig(join(workdir, "infectiousness.png"))
    close()


def plot_data(
    workdir: str,
    filename: str,
    grouped_data: list,
    state: int,
    obs: DataFrame,
    plot_cfg: dict,
    xlabel_str: str,
    ylabel_str: str,
    title_str: str,
    plot_weekly_data: bool,
    plot_percentile_flag: bool,
):
    """Plot individual state data

    Args:
        workdir (str): Working directory
        data_to_plot (DataFrame or list): Data to be plotted
        plot_increment (bool, optional): If plot the newly increased case. Defaults to True.
        obs (NoneorDataFrame, optional): If plot observations. Defaults to None.
        filename (str, optional): Output/figure filename. Defaults to "test.png".
        xlabel_str (str, optional): X-axis label. Defaults to "Step".
        ylabel_str (str, optional): Y-axis label. Defaults to "Total State".
        title_str (str, optional): Figure Title. Defaults to "Time series of total state value against step".
        plot_percentile_flag (bool, optional): If plot the percentile for ensemble. Defaults to False.
        plot_weekly_data (bool, optional): If convert daily data to weekly and plot. Defaults to True.
        plot_cfg (_type_, optional): Plot configuration. Defaults to {"linewidth": 0.5, "linestyle": "-"}.
        state_list (list, optional): Which state to plot. Defaults to [1, 2].
    """
    output = {}
    for i, proc_grouped in enumerate(grouped_data):

        proc_grouped_data = proc_grouped[state]

        if plot_weekly_data:
            proc_grouped_data = daily2weekly_data(proc_grouped_data)

        if state not in output:
            output[state] = []

        output[state].append(proc_grouped_data)

    if plot_percentile_flag:
        x = array(list(zip(*output[state]))).transpose()

        percentiles = {50: "r", 75: "g", 90: "b"}

        # Calculate percentiles
        data_percentiles = percentile(x, list(percentiles.keys()), axis=0)

        for i, percentile_key in enumerate(percentiles):
            plot(
                range(data_percentiles.shape[1]),
                data_percentiles[i, :],
                color=percentiles[percentile_key],
                label=percentile_key,
            )

    for state in output:
        for i, proc_grouped_data in enumerate(output[state]):
            if i == 0:
                plot(
                    proc_grouped_data,
                    color=VIS_COLOR[state],
                    label=f"{State(state).name}",
                    linewidth=plot_cfg["linewidth"],
                    linestyle=plot_cfg["linestyle"],
                )
            else:
                plot(
                    proc_grouped_data,
                    color=VIS_COLOR[state],
                    linewidth=plot_cfg["linewidth"],
                    linestyle=plot_cfg["linestyle"],
                )
    ref_data = proc_grouped_data
    if obs is not None:
        if plot_weekly_data:
            obs_to_plot = obs["weekly"]
        else:
            obs_to_plot = obs["daily"]
        # min_date = proc_grouped_data.index.min()
        # max_date = obs_to_plot.index.max()
        min_date = min(proc_grouped_data.index.min(), obs_to_plot.index.min())
        max_date = max(proc_grouped_data.index.max(), obs_to_plot.index.max())
        obs_to_plot = obs_to_plot.loc[
            (obs_to_plot.index >= min_date) & (obs_to_plot.index <= max_date)
        ]
        ref_data = obs_to_plot
        plot(obs_to_plot["Cases"], label="obs")

    downsample_factor = max(1, len(ref_data.index) // 10)

    # Select every nth element from the index
    downsampled_index = ref_data.index[::downsample_factor]

    xtick_labels = downsampled_index.strftime(
        "%m-%d"
    ).tolist()  # obs["Date"][-22:].tolist()
    xticks(downsampled_index, xtick_labels, rotation=45)

    xlabel(xlabel_str)
    ylabel(ylabel_str)
    title(title_str)
    legend()
    tight_layout()
    savefig(join(workdir, filename))
    close()