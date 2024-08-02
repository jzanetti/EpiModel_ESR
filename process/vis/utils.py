from logging import getLogger

from pandas import DataFrame

from process.model.disease import State

logger = getLogger()


def data_transformer(
    data_to_process: DataFrame, plot_increment: bool, state_list: list, use_dask: bool
):
    """Convert MESA output from accumulated state to newly produced state

    Args:
        data_to_plot (DataFrame): _description_
        plot_increment (bool): _description_
        state_list (list): _description_

    Returns:
        _type_: _description_
    """
    all_grouped = {}

    for state in state_list:
        state_key = "State"
        if plot_increment:
            state_key = f"{State(state).name.lower()}_flag"

        if isinstance(data_to_process, DataFrame):
            logger.info(f"Grouping ...")
            proc_data_to_plot = (
                data_to_process.groupby(["step", state_key])
                .size()
                .unstack(fill_value=0)
            )
            proc_data_to_plot.columns.name = None
            proc_data_to_plot = proc_data_to_plot[[1]]
            proc_data_to_plot = proc_data_to_plot.rename(columns={1: state})
            grouped = [proc_data_to_plot]
        else:
            grouped = []
            total_jobs = len(data_to_process)
            for i, proc_data_to_plot in enumerate(data_to_process):

                logger.info(f"Grouping {i} / {total_jobs} ...")

                proc_data_to_plot = proc_data_to_plot.groupby(
                    ["step", state_key]
                ).size()
                if use_dask:
                    proc_data_to_plot = proc_data_to_plot.compute()
                proc_data_to_plot = proc_data_to_plot.unstack(fill_value=0)

                proc_data_to_plot.columns.name = None
                proc_data_to_plot = proc_data_to_plot[[1]]
                proc_data_to_plot = proc_data_to_plot.rename(columns={1: state})
                grouped.append(proc_data_to_plot)

        all_grouped[state] = grouped

    return all_grouped
