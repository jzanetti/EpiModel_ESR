from logging import getLogger
from os.path import exists
from random import sample as random_sample

from dill import dump as dill_dump
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation
from pandas import DataFrame

from process import SAVED_MODEL_PATH
from process.model.disease import Agents, State
from process.model.weight import cal_reproduction_weight
from process.utils import (
    create_newly_increased_case,
    open_saved_model,
    read_syspop_data,
)

logger = getLogger()


def init_model(
    workdir: str,
    syspop_base_path: str or None,
    syspop_diary_path: str or None,
    syspop_address_path: str or None,
    syspop_healthcare_path: str or None,
    dhb_list: list or None,
    sample_ratio: float or None,
    overwrite_model: bool,
):
    """Initialize the model

    Args:
        workdir (str): Working directory
        syspop_base_path (strorNone): Synthetic population (base) data path
        syspop_diary_path (strorNone): Synthetic population (diary) data path
        syspop_address_path (strorNone): Synthetic population (address) data path
        dhb_list (listorNone): DHB list to be selected from
        sample_ratio (floatorNone): Interaction sample percentage
        overwrite_model (bool): If previous model is presented, we will rewrite it

    Returns:
        _type_: _description_
    """
    saved_model_path = SAVED_MODEL_PATH.format(workdir=workdir)

    if not exists(saved_model_path) or overwrite_model:
        data = read_syspop_data(
            syspop_base_path,
            syspop_diary_path,
            syspop_address_path,
            syspop_healthcare_path,
            sample_p=sample_ratio,
            dhb_list=dhb_list,
        )
        model = Epimodel_esr(data)
        model.save(saved_model_path)
    else:
        model = open_saved_model(saved_model_path)

    return model


class Epimodel_esr(Model):
    def __init__(self, model_data: DataFrame):
        syspop_base = model_data["syspop_base"]
        syspop_diary = model_data["syspop_diary"]
        syspop_address = model_data["syspop_address"]
        syspop_healthcare = model_data["syspop_healthcare"]
        self.grid = ContinuousSpace(
            x_max=syspop_address.latitude.max() + 0.1,
            y_max=syspop_address.longitude.max() + 0.1,
            torus=False,
            x_min=syspop_address.latitude.min() - 0.1,
            y_min=syspop_address.longitude.min() - 0.1,
        )
        self.schedule = RandomActivation(self)

        unique_ids = syspop_diary.id.unique()

        total_ids = len(unique_ids)

        for i, person_id in enumerate(unique_ids):

            proc_diary_locations = list(
                syspop_diary[syspop_diary.id == person_id].location.values
            )

            for proc_diary_location in proc_diary_locations:

                if proc_diary_location is None:
                    continue

                proc_address = syspop_address[
                    syspop_address.location == proc_diary_location
                ].drop_duplicates()

                if len(proc_address) == 0:
                    continue

                if i % 500 == 0.0:
                    logger.info(
                        f"Creating agents: {round(i/float(total_ids) * 100.0, 3)} %"
                    )

                proc_lat = proc_address.latitude.values
                proc_lon = proc_address.longitude.values
                proc_imms = syspop_healthcare[
                    syspop_healthcare.id == int(person_id.split("_")[0])
                ]["mmr"].values
                proc_type = syspop_diary[
                    (syspop_diary.id == person_id)
                    & (syspop_diary.location == proc_diary_location)
                ].type.values

                if (
                    len(proc_lat) > 1
                    or len(proc_lon) > 1
                    or len(proc_imms) > 1
                    or len(proc_type) > 1
                ):
                    raise Exception(
                        "Found same person (id_type) presents in multiple places ..."
                    )

                proc_person = Agents(
                    person_id,
                    self,
                    (
                        proc_lat[0],
                        proc_lon[0],
                    ),
                    proc_type[0],
                    proc_imms[0],
                )

                self.schedule.add(proc_person)
                self.grid.place_agent(proc_person, proc_person.pos)

        self.reproduction_weight = cal_reproduction_weight()

        self.datacollector = DataCollector(agent_reporters={"State": "state"})

    def initial_infection(
        self, initial_n: int, infection_time: int = 0, cleanup_agents: bool = False
    ):
        person_agents = [
            agent for agent in self.schedule.agents if isinstance(agent, Agents)
        ]
        if cleanup_agents:
            for agent in person_agents:
                agent.state = State.SUSCEPTIBLE
                agent.infection_time = None

        # Label selected agents as infected
        for agent in random_sample(person_agents, initial_n):
            agent.state = State.INFECTED
            agent.infection_time = infection_time

    def step(self, timestep):
        self.datacollector.collect(self)
        self.timestep = timestep
        self.schedule.step()

    def save(self, model_path: str):
        with open(model_path, "wb") as fid:
            dill_dump(self, fid)

    def postprocessing(self):
        all_agents = self.datacollector.get_agent_vars_dataframe()
        self.output = create_newly_increased_case(
            all_agents,
            list(all_agents["State"].unique()),
        )
