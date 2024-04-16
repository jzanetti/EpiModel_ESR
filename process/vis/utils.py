from pandas import DataFrame


def data_transformer(
    data_to_process: DataFrame, plot_increment: bool, state_list: list
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
            state_key = f"State_new_{state}"

        if isinstance(data_to_process, DataFrame):
            proc_data_to_plot = (
                data_to_process.groupby(["Step", state_key])
                .size()
                .unstack(fill_value=0)
            )
            proc_data_to_plot.columns.name = None
            proc_data_to_plot = proc_data_to_plot[[1]]
            proc_data_to_plot = proc_data_to_plot.rename(columns={1: state})
            grouped = [proc_data_to_plot]
        else:
            grouped = []
            for proc_data_to_plot in data_to_process:
                proc_data_to_plot = (
                    proc_data_to_plot.groupby(["Step", state_key])
                    .size()
                    .unstack(fill_value=0)
                )
                proc_data_to_plot.columns.name = None
                proc_data_to_plot = proc_data_to_plot[[1]]
                proc_data_to_plot = proc_data_to_plot.rename(columns={1: state})
                grouped.append(proc_data_to_plot)

        all_grouped[state] = grouped

    return all_grouped
