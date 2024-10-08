from datetime import datetime
from random import sample as random_sample
from random import uniform as random_uniform

from numpy import linspace as numpy_linspace
from pandas import DataFrame
from scipy.stats import gamma as scipy_gamma

from process import CLINICAL_PARAMS, TOTAL_TIMESTEPS
from process.model import Vaccine


def obtain_average_imms(
    person_agents: list, proc_vac_cfg: dict, target_ratio: float
) -> dict:
    """Obtain average immunisation in population

    Args:
        person_agents (list): all agents to be processed
        proc_vac_cfg (dict): vaccination configuration
        target_ratio (float): target immunisation rate

    Returns:
        dict: vaccination status
    """

    vac_status = {"nature": [], "full": [], "partial": [], "no": []}
    for id, proc_agent in enumerate(person_agents):

        ethnicity_flag = False
        if proc_agent.ethnicity in proc_vac_cfg[target_ratio]["ethnicity"]:
            ethnicity_flag = True

        age_flag = False
        for proc_age in proc_vac_cfg[target_ratio]["age"]:
            proc_age = proc_age.split("-")
            if proc_agent.age >= int(proc_age[0]) and proc_agent.age <= int(
                proc_age[1]
            ):
                age_flag = True
                break

        if (ethnicity_flag is False) or (age_flag is False):
            continue

        if proc_agent.vaccine_status.value == 0:
            vac_status["no"].append(id)
        elif proc_agent.vaccine_status.value == 1:
            vac_status["partial"].append(id)
        elif proc_agent.vaccine_status.value == 2:
            vac_status["full"].append(id)
        elif proc_agent.vaccine_status.value == 3:
            vac_status["nature"].append(id)

    imms = (
        len(vac_status["nature"]) + len(vac_status["full"]) + len(vac_status["partial"])
    )
    no_imms = len(vac_status["no"])
    total = imms + no_imms
    imms_ratio = imms / total

    return {"vac_status": vac_status, "imms_ratio": imms_ratio, "total": total}


def vaccination_adjustment(
    person_agents: list, intital_timestep: datetime, vac_measures_cfg: dict
) -> list:
    """Adjust orginal vaccination coverage using the setups from configuration

    Args:
        person_agents (list): all agents to be processed
        intital_timestep (datetime): the first timestep for the model
        vac_measures_cfg (dict): vaccination coverage configuration

    Returns:
        list: updated agents
    """
    for proc_vac_cfg in vac_measures_cfg:

        target_ratio = list(proc_vac_cfg.keys())[0]

        if not proc_vac_cfg[target_ratio]["enable"]:
            continue

        population_imms = obtain_average_imms(person_agents, proc_vac_cfg, target_ratio)

        if proc_vac_cfg[target_ratio]["operator"] == "fix":
            ratio_change = target_ratio - population_imms["imms_ratio"]
        elif proc_vac_cfg[target_ratio]["operator"] == "by":
            ratio_change = (
                population_imms["imms_ratio"] * target_ratio
                - population_imms["imms_ratio"]
            )

        if ratio_change > 0:  # we need to improve imms
            imms_time = proc_vac_cfg[target_ratio]["time"]
            people_ids = random_sample(
                population_imms["vac_status"]["no"],
                int(population_imms["total"] * ratio_change),
            )
            for proc_people_id in people_ids:
                person_agents[proc_people_id].vaccine_status = Vaccine.FULL
                if imms_time is not None:
                    person_agents[proc_people_id].imms_timestep = get_steps(
                        intital_timestep, str(imms_time)
                    )

        if ratio_change < 0:  # we need to remove imms
            people_ids = random_sample(
                population_imms["vac_status"]["full"]
                + population_imms["vac_status"]["partial"],
                int(population_imms["total"] * ratio_change),
            )
            for proc_people_id in people_ids:
                person_agents[proc_people_id].vaccine_status = Vaccine.NO

    return person_agents


def get_steps(intital_timestep: datetime, target_time: list) -> dict or int:
    """Get timesteps based on datetime

    Args:
        intital_timestep (datetime): _description_
        infection_time (list): _description_

    Returns:
        dict: _description_
    """

    if isinstance(target_time, str):
        if target_time.startswith("["):
            target_time = eval(target_time)
        else:
            target_time = datetime.strptime(target_time, "%Y%m%d")
            return (target_time - intital_timestep).days

    target_time_start = datetime.strptime(str(target_time[0]), "%Y%m%d")
    target_time_end = datetime.strptime(str(target_time[1]), "%Y%m%d")

    timestep_start = (target_time_start - intital_timestep).days
    timestep_end = (target_time_end - intital_timestep).days

    return {"start": timestep_start, "end": timestep_end}


def create_newly_increased_case(all_cases: DataFrame, state_list: list) -> DataFrame:
    """MESA output will give total infected cases at each time step,
    however, the ESR data only gives the newly reported cases for each week.
    Here we extract the newly infected cases (e.g., target_status == 1)from MESA output

    Args:
        all_cases (DataFrame): _description_
        target_status (int, optional): _description_. Defaults to 1.
    """
    all_cases = all_cases.reset_index()
    if 0 in state_list:
        state_list.remove(0)

    for target_state in state_list:
        all_cases[f"State_new_{target_state}"] = 0

    for target_state in state_list:
        newly_infected_ids = []
        for ts in range(TOTAL_TIMESTEPS):
            # Filter the DataFrame for the current timestep and where State transitions from 0 to 1
            proc_state_name = f"State_new_{target_state}"
            newly_infected = all_cases[
                (all_cases["Step"] == ts) & (all_cases["State"] == target_state)
            ][["Step", "AgentID", "State"]]
            newly_infected = newly_infected[
                ~newly_infected["AgentID"].isin(newly_infected_ids)
            ]

            newly_infected_ids.extend(list(newly_infected["AgentID"].values))

            newly_infected = newly_infected.rename(columns={"State": proc_state_name})
            all_cases.loc[newly_infected.index, proc_state_name] = newly_infected[
                proc_state_name
            ]
    for target_state in state_list:
        all_cases[f"State_new_{target_state}"][
            all_cases[f"State_new_{target_state}"] != 0
        ] = 1

    return all_cases


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


def cal_reproduction_weight(
    reproduction_rate: float = CLINICAL_PARAMS["reproduction_rate"],
    contact_weight: dict = {
        "school": 0.3,
        "household": 1.0,
        "outdoor": 0.01,
        "park": 0.01,
        "company": 0.5,
        "gym": 0.5,
        "kindergarten": 0.3,
        "supermarket": 0.1,
        "others": None,
        "fast_food": 0.15,
        "wholesale": 0.1,
        "department_store": 0.1,
        "restaurant": 0.3,
        "pub": 0.3,
        "cafe": 0.3,
    },
    use_fixed_weight: bool = True,
):
    """Create the reproduction weight for different social settings

    Args:
        reproduction_rate (float, optional): Reproduction rate. Defaults to 12.
        contact_weight (_type_, optional): Contact weight
            Defaults to {
                "school": 0.3,
                "household": 1.0,
                "outdoor": 0.01,
                "park": 0.01, ...
                "fast_food": 0.15,
                "wholesale": 0.1,
                ...}.
        use_fixed_weight (bool, optional): If use the fixed weight. Defaults to True.

    Returns:
        _type_: _description_
    """
    reproduction_weight = {}
    if use_fixed_weight:
        for contact_key in contact_weight:
            reproduction_weight[contact_key] = None
            if contact_weight[contact_key] is not None:
                reproduction_weight[contact_key] = reproduction_rate
        return reproduction_weight

    total_sum = 0
    for contact_key in contact_weight:
        if contact_weight[contact_key] is not None:
            total_sum += contact_weight[contact_key]

    weight = reproduction_rate / total_sum

    # Multiply all the values in the dictionary by 3.0
    for contact_key in contact_weight:
        reproduction_weight[contact_key] = None
        if contact_weight[contact_key] is not None:
            reproduction_weight[contact_key] = contact_weight[contact_key] * weight

    return reproduction_weight


def cal_infectiousness_profile(
    start_t: int = 10, end_t: int = 21, alpha: float = 0.2, beta: float = 2.0
) -> dict:

    infectiousness_profile = {}
    x = numpy_linspace(start_t, end_t, end_t - start_t + 1)
    y = scipy_gamma.pdf(x, alpha, scale=1 / beta)
    y = y / max(y)
    # Scale all the values in the dictionary up to 1.0
    for i, proc_t in enumerate(x):
        infectiousness_profile[int(proc_t)] = y[i]

    return infectiousness_profile
