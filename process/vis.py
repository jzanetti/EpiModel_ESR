from os.path import join
from random import sample as random_sample

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


def plot_grid(
    workdir: str,
    data_to_plot: DataFrame or list,
    state_list: list,
    plot_increment: bool = False,
    obs: None or DataFrame = None,
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
        plot(obs["Cases"].values[-180:], label="obs")
    xlabel("Step")
    ylabel("Total State")
    title("Time series of total state value against step")
    grid(True)
    legend()
    tight_layout()
    savefig(join(workdir, "test.png"))
    close()
