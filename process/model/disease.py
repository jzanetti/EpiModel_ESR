from enum import IntEnum
from logging import getLogger
from random import sample as random_sample
from random import uniform as random_uniform

from mesa import Agent
from numpy.random import choice as numpy_choice

from process import (
    CLINICAL_PARAMS,
    DEBUG_FLAG,
    INFECTED_NO_REPORT_RATIO,
    SET_REMOVED_PERCENTAGE,
)
from process.model import State, Vaccine
from process.model.utils import cal_infectiousness_profile, calculate_disease_days

logger = getLogger()


class Agents(Agent):
    def __init__(
        self,
        unique_id,
        person_attr,
        model,
        pos,
        loc_type,
        loc_type_value,
        imms_status,
        days_buffer: float = 0.15,
    ):
        super().__init__(unique_id, model)

        self.unique_id = unique_id
        self.age = person_attr["age"]
        self.ethnicity = person_attr["ethnicity"]
        self.gender = person_attr["gender"]
        self.pos = pos
        self.loc_type = loc_type
        self.loc_type_value = loc_type_value
        self.state = State.SUSCEPTIBLE
        if imms_status == "nature_imms":
            self.vaccine_status = Vaccine.NATURE
        if imms_status == "fully_imms":
            self.vaccine_status = Vaccine.FULL
        elif imms_status == "partial_imms":
            self.vaccine_status = Vaccine.PARTIAL
        elif imms_status == "no_imms":
            self.vaccine_status = Vaccine.NO

        self.vaccine_efficiency_full = CLINICAL_PARAMS["vaccine_efficiency"]["full"]
        self.vaccine_efficiency_partial = CLINICAL_PARAMS["vaccine_efficiency"][
            "partial"
        ]
        self.infection_time = None
        self.infection_src_type = None
        self.infection_src_venue = None
        self.symptomatic_time = None
        self.recovery_time = None
        days_buffer = random_uniform(0.0, days_buffer)

        for days_type in [
            "incubation",
            "infectiousness",
            "symptom",
            "recovered",
        ]:
            setattr(
                self,
                f"infection_to_{days_type}_days",
                calculate_disease_days(
                    CLINICAL_PARAMS[f"infection_to_{days_type}_days"], days_buffer
                ),
            )

        self.infectiousness_profile = cal_infectiousness_profile(
            start_t=self.infection_to_infectiousness_days["start"],
            end_t=self.infection_to_infectiousness_days["end"],
            alpha=9.0,
            beta=0.5,
        )

    def infected_the_same_agents(self, cur_diary_id):
        for proc_agent in self.model.agents:
            if (
                proc_agent.unique_id.startswith(cur_diary_id.split("_")[0])
                and proc_agent.unique_id != cur_diary_id
            ):
                if proc_agent.state == State.SUSCEPTIBLE:
                    proc_agent.state = State.INFECTED
                    proc_agent.infection_time = self.model.timestep

    def step(self):

        if self.state == State.SEED_INFECTION:
            if self.model.timestep == self.infection_time:
                self.state = State.INFECTED
                if DEBUG_FLAG:
                    logger.info(f"    * intial infection at {self.model.timestep}")

        if self.state in [State.INFECTED, State.INFECTED_NO_REPORT]:

            delta_t = self.model.timestep - self.infection_time

            # --------------------------------------------
            # Step 0: Infected the same agent but in a different place
            # ---------------------------------------------
            self.infected_the_same_agents(self.unique_id)

            # --------------------------------------------
            # Step 1: Check if the agent is recovered
            # ---------------------------------------------
            if delta_t > self.infection_to_recovered_days:
                self.state = State.RECOVERED
                return

            # --------------------------------------------
            # Step 2: Check if the agent is infectiousness,
            #          if not, nothing will be done from here
            # ---------------------------------------------
            if (
                delta_t < self.infection_to_infectiousness_days["start"]
                or delta_t > self.infection_to_infectiousness_days["end"]
            ):
                return

            # --------------------------------------------
            # Step 3: Check if the agent has symptoms,
            #          if so there is a chance he/she may stay at home,
            # ---------------------------------------------
            if self.model.stay_at_home_if_symptom["enable"]:
                if (
                    delta_t > self.infection_to_symptom_days["start"]
                    or delta_t < self.infection_to_symptom_days["end"]
                ):
                    if numpy_choice(
                        [True, False],
                        p=[
                            self.model.stay_at_home_if_symptom["percentage"],
                            1.0 - self.model.stay_at_home_if_symptom["percentage"],
                        ],
                    ):
                        return

            # --------------------------------------------
            # Step 4: Creating infectiousness profile
            # ---------------------------------------------
            if self.model.reproduction_weight[self.loc_type] is None:
                return
            try:
                infectiousness_value = (
                    self.infectiousness_profile[delta_t]
                    * self.model.reproduction_weight[self.loc_type]
                )
            except KeyError:
                infectiousness_value = 0.0

            # --------------------------------------------
            # Step 5: Getting all possible neighbors
            # ---------------------------------------------
            all_neighbors = self.model.grid.get_neighbors(
                self.pos, 0.0, include_center=True
            )

            # --------------------------------------------
            # Step 6: Infecting people if they are not vaccinated
            # ---------------------------------------------
            neighbors = random_sample(
                all_neighbors, min([len(all_neighbors), int(infectiousness_value)])
            )
            infected_neighbors = []
            for neighbor in neighbors:

                if neighbor.unique_id == self.unique_id:
                    continue

                # --------------------------------------------
                # Step 6.1: Remove some neigbors permanently
                # ---------------------------------------------
                try:
                    removed_ratio = SET_REMOVED_PERCENTAGE[self.loc_type]
                except KeyError:
                    removed_ratio = SET_REMOVED_PERCENTAGE["default"]

                if numpy_choice(
                    [True, False],
                    p=[
                        removed_ratio,
                        1.0 - removed_ratio,
                    ],
                ):
                    neighbor.state = State.REMOVED
                    continue

                # --------------------------------------------
                # Step 6.2: Infecting neighbors
                # ---------------------------------------------
                if neighbor.state == State.SUSCEPTIBLE:

                    if neighbor.vaccine_status == Vaccine.NO or (
                        neighbor.imms_timestep is not None
                        and neighbor.imms_timestep > self.model.timestep
                    ):

                        if numpy_choice(
                            [True, False],
                            p=[
                                INFECTED_NO_REPORT_RATIO,
                                1.0 - INFECTED_NO_REPORT_RATIO,
                            ],
                        ):
                            neighbor.state = State.INFECTED_NO_REPORT
                        else:
                            neighbor.state = State.INFECTED
                        neighbor.infection_time = self.model.timestep
                        infected_neighbors.append(neighbor)

                    elif neighbor.vaccine_status in [Vaccine.FULL, Vaccine.PARTIAL]:

                        if neighbor.vaccine_status == Vaccine.FULL:
                            proc_vaccine_efficiency = self.vaccine_efficiency_full
                        else:
                            proc_vaccine_efficiency = self.vaccine_efficiency_partial

                        if numpy_choice(
                            [True, False],
                            p=[
                                1.0 - proc_vaccine_efficiency,
                                proc_vaccine_efficiency,
                            ],
                        ):

                            if numpy_choice(
                                [True, False],
                                p=[
                                    INFECTED_NO_REPORT_RATIO,
                                    1.0 - INFECTED_NO_REPORT_RATIO,
                                ],
                            ):
                                neighbor.state = State.INFECTED_NO_REPORT
                            else:
                                neighbor.state = State.INFECTED

                            neighbor.infection_time = self.model.timestep
                            infected_neighbors.append(neighbor)

                    elif neighbor.vaccine_status == Vaccine.NATURE:
                        continue

            if len(infected_neighbors) > 0:
                for infected_neighbor in infected_neighbors:
                    infected_neighbor.infection_src_type = self.loc_type
                    infected_neighbor.infection_src_venue = self.loc_type_value

                if DEBUG_FLAG:
                    logger.info(
                        f"    * {self.loc_type}/{self.loc_type_value}: newly infected person: {len(infected_neighbors)}"
                    )
