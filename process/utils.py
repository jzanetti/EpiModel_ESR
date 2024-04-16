from datetime import datetime
from logging import INFO, Formatter, StreamHandler, basicConfig, getLogger
from os.path import exists, join
from pickle import dump as pickle_dump
from pickle import load as pickle_load
from random import uniform as random_uniform

from dill import load as dill_load
from numpy import round as numpy_round
from pandas import DataFrame
from pandas import concat as pandas_concat
from pandas import date_range
from pandas import isna as pandas_isna
from pandas import merge as pandas_merge
from pandas import read_parquet
from pandas import read_parquet as pandas_read_parquet
from pandas import to_datetime, to_numeric
from yaml import safe_load as yaml_safe_load

from process import DIARY_TYPES, SA2_DATA_PATH, TOTAL_TIMESTEPS

logger = getLogger()


def weekly2daily_data(weekly_data: DataFrame, target_var: str = "Cases") -> DataFrame:
    """Covert weekly data (e.g., obs) to daily data

    Args:
        weekly_data (DataFrame): _description_
        target_var (str, optional): _description_. Defaults to "Cases".

    Returns:
        DataFrame: _description_
    """

    if weekly_data.index.name != "Date":
        weekly_data.set_index("Date", inplace=True)

    # Resample to daily
    daily_data = weekly_data.resample("D").ffill()

    # Distribute weekly values evenly across days
    for week, group in daily_data.groupby(daily_data.index.strftime("%U")):

        weekly_value = weekly_data.loc[
            weekly_data.index.strftime("%U") == week, target_var
        ].iloc[0]
        num_days = len(group)
        if not pandas_isna(weekly_value):
            daily_data.loc[daily_data.index.strftime("%U") == week, target_var] = (
                numpy_round(weekly_value / num_days, 1)
            )
    return daily_data


def daily2weekly_data(data_to_process: DataFrame):
    return data_to_process.resample("W").sum()


def read_obs(
    obs_path: str, DHB_list: list, resample_flag: bool = True, ref_year: int = 2019
):
    """Read observation data

    Args:
        obs_path (str): _description_
        DHB_list (list): _description_
        resample_flag (bool, optional): _description_. Defaults to True.
    """

    def _week_to_date(year, week):
        return to_datetime(f"{year} {week} 1", format="%Y %U %w")

    obs = pandas_read_parquet(obs_path)
    obs = obs[obs["Region"].isin(DHB_list)]
    obs = obs.melt(id_vars=["Region"], var_name="Week", value_name="Cases")
    obs["Date"] = obs["Week"].apply(
        lambda x: _week_to_date(ref_year, int(x.split("_")[1]))
    )
    obs["Cases"] = to_numeric(obs["Cases"], errors="coerce")
    obs.set_index("Date", inplace=True)
    # obs = obs.resample("D").interpolate(method="linear")
    obs.reset_index(inplace=True)
    obs = obs[["Date", "Cases"]]

    obs.set_index("Date", inplace=True)

    obs_daily = None
    if resample_flag:
        obs = obs.resample("W").sum()
        obs_daily = weekly2daily_data(obs)

    return {"weekly": obs, "daily": obs_daily}


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


def sample_syspop_diary_with_all_household(
    syspop_diary: DataFrame, sample_p: float
) -> DataFrame:
    """Sample syspop diary but keep all households

    Args:
        syspop_diary (DataFrame): Syspop diary dataset
        sample_p (float): Sample percentage

    Returns:
        Dataframe: Updated Syspop
    """
    type_household_rows = syspop_diary[syspop_diary["type"] == "household"]
    other_type_rows = syspop_diary[~syspop_diary["type"].isin(["household"])]
    other_type_selected = other_type_rows.sample(frac=sample_p, replace=False)
    selected_rows = pandas_concat([type_household_rows, other_type_selected])
    selected_rows = selected_rows.reset_index()
    return selected_rows


def read_syspop_data(
    syspop_base_path: str,
    syspop_diary_path: str,
    syspop_address_path: str,
    syspop_healthcare_path: str,
    obs_path: str or None,
    dhb_list: list or None = None,
    sample_p: float or None = 0.01,
    sample_all_hhd_flag: bool = True,
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
    syspop_healthcare = pandas_read_parquet(syspop_healthcare_path)
    syspop_address = pandas_read_parquet(syspop_address_path)
    syspop_address = syspop_address[["name", "latitude", "longitude"]]
    syspop_address = syspop_address.rename(columns={"name": "location"})

    syspop_diary = syspop_diary[syspop_diary["type"].isin(DIARY_TYPES)]

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

        syspop_healthcare = syspop_healthcare[
            syspop_healthcare["id"].isin(syspop_base.id)
        ].reset_index()[["id", "mmr"]]

    if sample_p is not None:
        # sample_size = int(sample_p * len(syspop_diary))
        # logger.info(f"Selected {sample_size} samples ...")
        # syspop_diary = syspop_diary.sample(sample_size, random_state=sample_seed)
        if sample_all_hhd_flag:
            syspop_diary = sample_syspop_diary_with_all_household(
                syspop_diary, sample_p
            )
        else:
            syspop_diary = syspop_diary.sample(int(sample_p * len(syspop_diary)))
        logger.info(f"Selected {len(syspop_diary)} samples ...")

    syspop_address = syspop_address[
        syspop_address["location"].isin(syspop_diary.location)
    ].reset_index()[["location", "latitude", "longitude"]]

    syspop_diary["id_type"] = (
        syspop_diary["id"].astype(str) + "_" + syspop_diary["type"]
    )

    syspop_diary = syspop_diary[["id_type", "type", "location"]].rename(
        columns={"id_type": "id"}
    )

    obs = None
    if obs_path is not None:
        obs = read_obs(obs_path, dhb_list)

    return {
        "syspop_base": syspop_base,
        "syspop_diary": syspop_diary,
        "syspop_address": syspop_address,
        "syspop_healthcare": syspop_healthcare,
        "obs": obs,
    }


def read_cfg(cfg_path: str, task_name: str) -> dict:

    with open(cfg_path, "r") as file:
        cfg = yaml_safe_load(file)

    if task_name in ["create_model", "run_vis"]:
        return cfg["create_model"]

    if task_name == "run_model":
        return cfg["run_sims"]
