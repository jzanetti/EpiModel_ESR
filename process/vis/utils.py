from logging import getLogger

from pandas import DataFrame

from process.model.disease import State

logger = getLogger()
from PIL import Image


def data_transformer_spread(
    spread_dataset: DataFrame, data_to_plot_for_spread: DataFrame
):
    """Data transformaing for the spread vis

    Args:
        spread_dataset (DataFrame): _description_
        data_to_plot_for_spread (DataFrame): _description_

    Raises:
        Exception: _description_

    Returns:
        _type_: _description_
    """
    diary_data = spread_dataset["diary"][["id", "type", "location"]].drop_duplicates()
    address_data = spread_dataset["address"][
        ["name", "latitude", "longitude"]
    ].drop_duplicates()
    all_timesteps = data_to_plot_for_spread.step.unique()
    spread_data_to_plot = {"id": [], "time": [], "latitude": [], "longitude": []}
    len_timesteps = len(all_timesteps)
    for i_ts, proc_ts in enumerate(all_timesteps):

        logger.info(f"Generating spread map data for {i_ts}/{len_timesteps}")

        proc_data = data_to_plot_for_spread[data_to_plot_for_spread["step"] == proc_ts]
        proc_data_infected = proc_data[proc_data["infected_flag"] == 1]
        if len(proc_data_infected) == 0:
            continue

        for _, proc_infectee in proc_data_infected.iterrows():
            proc_infectee_location_name = (
                diary_data[
                    (diary_data["id"] == int(proc_infectee.id))
                    & (diary_data["type"] == proc_infectee.location)
                ]["location"]
                .drop_duplicates()
                .values[0]
            )

            if proc_infectee_location_name == "nan":
                continue

            proc_infectee_location_address = address_data[
                address_data["name"] == proc_infectee_location_name
            ]

            if len(proc_infectee_location_address) > 1:
                raise Exception("Household address error ...")

            spread_data_to_plot["time"].append(proc_ts)

            spread_data_to_plot["latitude"].append(
                proc_infectee_location_address["latitude"].values[0]
            )

            spread_data_to_plot["longitude"].append(
                proc_infectee_location_address["longitude"].values[0]
            )
            spread_data_to_plot["id"].append(int(proc_infectee.id))

    return DataFrame(spread_data_to_plot)


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


def convert_png_to_gif(png_files, gif_path, duration):
    # Read all png images into a list
    images = [Image.open(png_file) for png_file in png_files]

    # Save the images as a GIF
    images[0].save(
        gif_path, save_all=True, append_images=images[1:], duration=duration, loop=0
    )
