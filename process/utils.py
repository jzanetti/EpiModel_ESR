from datetime import datetime
from logging import INFO, Formatter, StreamHandler, basicConfig, getLogger
from os.path import exists, join
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from random import uniform as random_uniform

from dill import load as dill_load
from pandas import DataFrame
from pandas import concat as pandas_concat
from pandas import merge as pandas_merge
from pandas import read_parquet
from pandas import read_parquet as pandas_read_parquet
from pandas import to_datetime, to_numeric

from process import SA2_DATA_PATH

logger = getLogger()


def read_obs(obs_path: str, DHB_list: list):

    def _week_to_date(year, week):
        return to_datetime(f"{year} {week} 1", format="%Y %U %w")

    obs = pandas_read_parquet(obs_path)
    obs = obs[obs["Region"].isin(DHB_list)]
    obs = obs.melt(id_vars=["Region"], var_name="Week", value_name="Cases")
    obs["Date"] = obs["Week"].apply(lambda x: _week_to_date(2024, int(x.split("_")[1])))
    obs["Cases"] = to_numeric(obs["Cases"], errors="coerce")
    obs.set_index("Date", inplace=True)
    obs = obs.resample("D").interpolate(method="linear")
    obs.reset_index(inplace=True)
    obs = obs[["Date", "Cases"]]

    return obs


def open_saved_model(model_path: str):

    with open(model_path, "rb") as f:
        model = dill_load(f)

    return model


def setup_logging(
    workdir: str = "/tmp",
    log_type: str = "epimodel_esr",
    start_utc: datetime = datetime.utcnow(),
):
    """set up logging system for tasks

    Returns:
        object: a logging object
    """
    formatter = Formatter(
        "%(asctime)s - %(name)s.%(lineno)d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch = StreamHandler()
    ch.setLevel(INFO)
    ch.setFormatter(formatter)
    logger_path = join(workdir, f"{log_type}.{start_utc.strftime('%Y%m%d')}")
    basicConfig(filename=logger_path),
    logger = getLogger()
    logger.setLevel(INFO)
    logger.addHandler(ch)

    return logger


def get_sa2_from_dhb(dhb_list):
    sa2_to_dhb = pandas_read_parquet(SA2_DATA_PATH)

    sa2_to_dhb = sa2_to_dhb[sa2_to_dhb["DHB_name"].isin(dhb_list)]

    return list(sa2_to_dhb["SA2"].unique())


def calculate_disease_days(days: int, buffer: float):
    """Create the disease days buffer

    Args:
        days (int): _description_
        buffer (float): _description_
    """
    if isinstance(days, dict):
        return {
            "start": round(days["start"] * (1 - buffer)),
            "end": round(days["end"] * (1 + buffer)),
        }
    else:
        return random_uniform(days * (1 - buffer), days * (1 + buffer))


def read_syspop_data(
    syspop_base_path: str,
    syspop_diary_path: str,
    syspop_address_path: str,
    dhb_list: list or None = None,
    sample_p: float or None = 0.01,
    sample_seed: int or None = None,
) -> DataFrame:
    """Read required input synthetic population data

    Args:
        workdir (str): Working directory
        syspop_base_path (str): Synthetic population base data
        syspop_diary_path (str): Synthetic population diary data
        syspop_address_path (str): Synthetic population address data
        dhb_list (list): DHB list to be used
        sample_p (float): Sample percentage
        sample_seed (int): Sample seed. Default: 10

    Returns:
        dict: decoded data
    """

    logger.info("Start processing input ... ")
    syspop_base = pandas_read_parquet(syspop_base_path)
    syspop_diary = pandas_read_parquet(syspop_diary_path)
    syspop_address = pandas_read_parquet(syspop_address_path)
    syspop_address = syspop_address[["name", "latitude", "longitude"]]
    syspop_address = syspop_address.rename(columns={"name": "location"})

    syspop_diary = (
        syspop_diary[["id", "type", "location"]]
        .drop_duplicates()
        .reset_index()[["id", "type", "location"]]
    )

    if dhb_list is not None:
        selected_sa2 = get_sa2_from_dhb(dhb_list)

        syspop_base = syspop_base[syspop_base["area"].isin(selected_sa2)].reset_index()[
            ["id", "area", "age", "gender", "ethnicity"]
        ]
        syspop_diary = syspop_diary[
            syspop_diary["id"].isin(syspop_base.id)
        ].reset_index()[["id", "type", "location"]]

    if sample_p is not None:
        sample_size = int(sample_p * len(syspop_diary))
        logger.info(f"Selected {sample_size} samples ...")
        syspop_diary = syspop_diary.sample(sample_size, random_state=sample_seed)

    syspop_address = syspop_address[
        syspop_address["location"].isin(syspop_diary.location)
    ].reset_index()[["location", "latitude", "longitude"]]

    syspop_diary["id_type"] = (
        syspop_diary["id"].astype(str) + "_" + syspop_diary["type"]
    )

    syspop_diary = syspop_diary[["id_type", "type", "location"]].rename(
        columns={"id_type": "id"}
    )

    return {
        "syspop_base": syspop_base,
        "syspop_diary": syspop_diary,
        "syspop_address": syspop_address,
    }
