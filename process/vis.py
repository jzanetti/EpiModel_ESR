import networkx as nx
from matplotlib.pyplot import (
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
from pandas import DataFrame

from process.model.disease import State


def plot_grid(data_to_plot: DataFrame, state_list: list):
    # Group by 'Step' and calculate the sum of 'State'
    grouped = data_to_plot.groupby(["Step", "State"]).size().unstack(fill_value=0)

    # Plot the result
    figure(figsize=(10, 6))
    for state in grouped.columns:
        if state not in state_list:
            continue
        plot(grouped.index, grouped[state], label=f"{State(state).name}")
    xlabel("Step")
    ylabel("Total State")
    title("Time series of total state value against step")
    grid(True)
    legend()
    tight_layout()
    savefig("test.png")
