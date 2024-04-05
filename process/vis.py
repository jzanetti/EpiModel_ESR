from os.path import join

from matplotlib.pyplot import (
    close,
    figure,
    grid,
    legend,
    plot,
    savefig,
    tight_layout,
    title,
    xlabel,
    ylabel,
)
from mesa.agent import AgentSet as mesa_agentset
from pandas import DataFrame

from process import VIS_COLOR
from process.model.disease import State


def plot_infectiousness_profile(workdir: str, model_agents: mesa_agentset):
    for proc_agent in model_agents:
        proc_infectiousness_profile = proc_agent.infectiousness_profile
        plot(
            list(proc_infectiousness_profile.keys()),
            list(proc_infectiousness_profile.values()),
            linestyle="-",
            color="k",
        )
    xlabel("Step")
    ylabel("Infectiousness")
    title("Infectiousness Factor")
    grid(True)
    legend()
    tight_layout()
    savefig(join(workdir, "infectiousness.png"))
    close()


def plot_grid(
    workdir: str,
    data_to_plot: DataFrame or list,
    state_list: list,
    obs: None or DataFrame = None,
):
    # Group by 'Step' and calculate the sum of 'State'

    if isinstance(data_to_plot, DataFrame):
        grouped = [data_to_plot.groupby(["Step", "State"]).size().unstack(fill_value=0)]
    else:
        grouped = []
        for proc_data_to_plot in data_to_plot:
            grouped.append(
                proc_data_to_plot.groupby(["Step", "State"])
                .size()
                .unstack(fill_value=0)
            )

    # Plot the result
    figure(figsize=(10, 6))

    for i, proc_grouped in enumerate(grouped):
        for state in proc_grouped.columns:
            if state not in state_list:
                continue
            if i == 0:
                plot(
                    proc_grouped.index,
                    proc_grouped[state],
                    color=VIS_COLOR[state],
                    label=f"{State(state).name}",
                )
            else:
                plot(
                    proc_grouped.index,
                    proc_grouped[state],
                    color=VIS_COLOR[state],
                )

    if obs is not None:
        plot(obs["Cases"].values[-180:] * 10, label="obs")
    xlabel("Step")
    ylabel("Total State")
    title("Time series of total state value against step")
    grid(True)
    legend()
    tight_layout()
    savefig(join(workdir, "test.png"))
    close()
