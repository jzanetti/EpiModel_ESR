from pandas import DataFrame

from process.vis.utils import data_transformer
from process.vis.vis import plot_data, plot_infectiousness_profile


def plot_wrapper(
    workdir: str,
    data_to_plot: DataFrame or list,
    plot_increment: bool = True,
    obs: None or DataFrame = None,
    agents: None or DataFrame = None,
    filename: str = "test",
    xlabel_str: str = "Step",
    ylabel_str: str = "Total State",
    title_str: str = "Time series of total state value against step",
    plot_percentile_flag: bool = False,
    plot_weekly_data: bool = True,
    plot_cfg: dict = {"linewidth": 0.5, "linestyle": "-"},
    state_list: list = [1, 2],
):
    """Plot timeseries such as infection and its comparisons with obs

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
    if agents is not None:
        plot_infectiousness_profile(workdir, agents)

    all_grouped = data_transformer(data_to_plot, plot_increment, state_list)

    filename_suffix = "daily"
    if plot_weekly_data:
        filename_suffix = "weekly"

    for proc_state in state_list:
        plot_data(
            workdir,
            f"{filename}_state{proc_state}_{filename_suffix}.png",
            all_grouped[proc_state],
            proc_state,
            obs,
            plot_cfg,
            xlabel_str,
            ylabel_str,
            title_str,
            plot_weekly_data,
            plot_percentile_flag,
        )
