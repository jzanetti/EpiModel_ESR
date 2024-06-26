from datetime import datetime
from logging import getLogger
from os.path import exists
from random import randint as random_randint
from random import sample as random_sample

from dill import dump as dill_dump
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.space import ContinuousSpace
from mesa.time import RandomActivation
from numpy import int8
from pandas import DataFrame
from pandas import to_timedelta as pandas_to_timedelta

from process.model import State, Vaccine
from process.model.disease import Agents
from process.model.utils import (
    cal_reproduction_weight,
    create_newly_increased_case,
    get_steps,
    vaccination_adjustment,
)

logger = getLogger()


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

                person_attr = syspop_base[
                    syspop_base.id == int(person_id.split("_")[0])
                ]
                if len(person_attr) != 1:
                    raise Exception("Found confusing agents from the dataset ...")

                person_attr = {
                    "age": person_attr.age.values[0],
                    "gender": person_attr.gender.values[0],
                    "ethnicity": person_attr.ethnicity.values[0],
                }

                proc_person = Agents(
                    person_id,
                    person_attr,
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

        self.stay_at_home_if_symptom = None

    def measures(self, intital_timestep: datetime, vac_cfg: dict):
        person_agents = [
            agent for agent in self.schedule.agents if isinstance(agent, Agents)
        ]

        # --------------------------------
        # Stay at home if symptom
        # --------------------------------
        self.stay_at_home_if_symptom = vac_cfg["stay_at_home_if_symptom"]

        # --------------------------------
        # Vaccination adjustment
        # --------------------------------
        vaccination_adjustment(person_agents, intital_timestep, vac_cfg["vaccine"])

    def initial_infection(
        self,
        initial_infection: dict,
        intital_timestep: datetime,
        cleanup_agents: bool = False,
    ):
        person_agents = [
            agent for agent in self.schedule.agents if isinstance(agent, Agents)
        ]

        if cleanup_agents:
            for agent in person_agents:
                agent.state = State.SUSCEPTIBLE
                agent.infection_time = None
                agent.imms_timestep = None

        for proc_infection in initial_infection:

            initial_n = list(proc_infection.keys())[0]
            proc_sampled_agents = random_sample(person_agents, initial_n)
            proc_infection_time = proc_infection[initial_n]

            for agent in proc_sampled_agents:
                agent.state = State.SEED_INFECTION
                proc_ts = get_steps(intital_timestep, proc_infection_time)
                agent.infection_time = random_randint(proc_ts["start"], proc_ts["end"])
            self.initial_infected = proc_sampled_agents

    def step(self, timestep):
        self.timestep = timestep
        # self.datacollector.collect(self)
        self.schedule.step()
        self.datacollector.collect(self)

    def save(self, model_path: str):
        with open(model_path, "wb") as fid:
            dill_dump(self, fid)

    def postprocessing(self, intital_timestep):
        all_agents = self.datacollector.get_agent_vars_dataframe()
        decoded_output = create_newly_increased_case(
            all_agents,
            list(all_agents["State"].unique()),
        )
        if intital_timestep is not None:
            # decoded_output["Step"] = pandas_to_datetime(
            #    intital_timestep, format="%Y%m%d"
            # ) + pandas_to_timedelta(decoded_output["Step"], unit="D")
            decoded_output["Step"] = intital_timestep + pandas_to_timedelta(
                decoded_output["Step"], unit="D"
            )

        all_states = list(all_agents["State"].unique())
        all_states.remove(0)
        for proc_state in all_states:
            decoded_output[f"State_new_{proc_state}"] = decoded_output[
                f"State_new_{proc_state}"
            ].astype(int8)
        decoded_output["State"] = decoded_output["State"].astype(int8)

        self.output = decoded_output
