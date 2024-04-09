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


def vis_data_transformer(
    data_to_plot: DataFrame,
    plot_increment: bool,
):
    state_key = "State"
    if plot_increment:
        state_key = "State_new"

    if isinstance(data_to_plot, DataFrame):
        grouped = [
            data_to_plot.groupby(["Step", state_key]).size().unstack(fill_value=0)
        ]
    else:
        grouped = []
        for proc_data_to_plot in data_to_plot:
            grouped.append(
                proc_data_to_plot.groupby(["Step", state_key])
                .size()
                .unstack(fill_value=0)
            )
    return grouped


def plot_grid(
    workdir: str,
    data_to_plot: DataFrame or list,
    state_list: list,
    plot_increment: bool = False,
    obs: None or DataFrame = None,
    filename: str = "test.png",
    xlabel_str: str = "Step",
    ylabel_str: str = "Total State",
    title_str: str = "Time series of total state value against step",
    plot_percentile_flag: bool = False,
    plot_weekly_data: bool = True,
):
    grouped = vis_data_transformer(data_to_plot, plot_increment)

    output = {}
    for i, proc_grouped in enumerate(grouped):
        for state in proc_grouped.columns:
            if state not in state_list:
                continue

            proc_grouped_data = proc_grouped[state]
            proc_grouped_index = proc_grouped_data.index

            if plot_weekly_data:
                proc_grouped_data, proc_grouped_index = daily2weekly_data(
                    proc_grouped_data
                )

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
                    proc_grouped_index,
                    proc_grouped_data,
                    color=VIS_COLOR[state],
                    label=f"{State(state).name}",
                    linewidth=0.5,
                )
            else:
                plot(
                    proc_grouped_index,
                    proc_grouped_data,
                    color=VIS_COLOR[state],
                    linewidth=0.5,
                )

    if obs is not None:
        plot(obs["Cases"].values[-22:], label="obs")

    xlabel(xlabel_str)
    ylabel(ylabel_str)
    title(title_str)
    grid(True)
    legend()
    tight_layout()
    savefig(join(workdir, filename))
    close()
