from logging import getLogger
from random import sample as random_sample

from dill import dump as dill_dump
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation
from pandas import DataFrame

from process.model.disease import Agents, State
from process.model.weight import cal_reproduction_weight

logger = getLogger()


class Epimodel_esr(Model):
    def __init__(
        self, model_data: DataFrame, initial_n: int, width: int = 10, height: int = 10
    ):
        syspop_base = model_data["syspop_base"]
        syspop_diary = model_data["syspop_diary"]
        syspop_address = model_data["syspop_address"]
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

            proc_diary_location = syspop_diary[
                syspop_diary.id == person_id
            ].location.values[0]

            proc_address = syspop_address[
                syspop_address.location == proc_diary_location
            ]

            if len(proc_address) == 0:
                continue

            if i % 500 == 0.0:
                logger.info(
                    f"Creating agents: {round(i/float(total_ids) * 100.0, 3)} %"
                )

            proc_lat = proc_address.latitude.values
            proc_lon = proc_address.longitude.values

            # if len(proc_lat) > 1 or len(proc_lon) > 1:
            #    raise Exception(
            #        "Found same person (id_type) presents in multiple places ..."
            #    )

            proc_person = Agents(
                person_id,
                self,
                (
                    proc_lat[0],
                    proc_lon[0],
                ),
                syspop_diary[syspop_diary.id == person_id].type.values[0],
            )

            self.schedule.add(proc_person)
            self.grid.place_agent(proc_person, proc_person.pos)

        self.reproduction_weight = cal_reproduction_weight()

        # make some agents infected at start
        person_agents = [
            agent for agent in self.schedule.agents if isinstance(agent, Agents)
        ]

        # Label selected agents as infected
        for agent in random_sample(person_agents, initial_n):
            agent.state = State.INFECTED
            agent.infection_time = -7

        self.datacollector = DataCollector(agent_reporters={"State": "state"})

    def step(self, timestep):
        self.datacollector.collect(self)
        self.timestep = timestep
        self.schedule.step()

    def save(self, model_path: str):
        with open(model_path, "wb") as fid:
            dill_dump(self, fid)
