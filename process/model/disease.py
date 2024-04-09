from enum import IntEnum
from logging import getLogger
from random import sample as random_sample
from random import uniform as random_uniform

from mesa import Agent
from numpy.random import choice as numpy_choice

from process import CLINICAL_PARAMS, DEBUG_FLAG, INFECTED_NO_REPORT_RATIO, MEASURES
from process.model.weight import cal_infectiousness_profile
from process.utils import calculate_disease_days

logger = getLogger()


class State(IntEnum):
    SUSCEPTIBLE = 0
    SEED_INFECTION = 1
    INFECTED = 2
    RECOVERED = 3
    INFECTED_NO_REPORT = 4


class Vaccine(IntEnum):
    NATURE = 3
    FULL = 2
    PARTIAL = 1
    NO = 0


class Agents(Agent):
    def __init__(
        self,
        unique_id,
        model,
        pos,
        loc_type,
        imms_status,
        infection_to_incubation_days: list = [0, 10],
        infection_to_infectiousness_days: list = [10, 21],
        infection_to_symptom_days: list = [11, 20],
        infection_to_recovered_days: int = 21,
        days_buffer: float = 0.15,
    ):
        super().__init__(unique_id, model)

        self.unique_id = unique_id
        self.age = self.random.normalvariate(20, 40)
        self.pos = pos
        self.loc_type = loc_type
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

    def step(self):

        if self.state == State.SEED_INFECTION:
            if self.model.timestep == self.infection_time:
                self.state = State.INFECTED

        if self.state in [State.INFECTED, State.INFECTED_NO_REPORT]:

            delta_t = self.model.timestep - self.infection_time

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
            if MEASURES["stay_at_home_if_symptom"]["enable"]:
                if (
                    delta_t > self.infection_to_symptom_days["start"]
                    or delta_t < self.infection_to_symptom_days["end"]
                ):
                    if numpy_choice(
                        [True, False],
                        p=[
                            MEASURES["stay_at_home_if_symptom"]["percentage"],
                            1.0 - MEASURES["stay_at_home_if_symptom"]["percentage"],
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
            neighbors = self.model.grid.get_neighbors(
                self.pos, 0.0, include_center=True
            )
            neighbors = random_sample(
                neighbors, min([len(neighbors), int(infectiousness_value)])
            )

            # --------------------------------------------
            # Step 5: Infecting people if they are not vaccinated
            # ---------------------------------------------
            infected_neighbors = []
            for neighbor in neighbors:

                if neighbor.unique_id == self.unique_id:
                    continue

                if neighbor.state == State.SUSCEPTIBLE:
                    if neighbor.vaccine_status == Vaccine.NO:

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

            if len(infected_neighbors) > 0 and DEBUG_FLAG:
                logger.info(
                    f"    * {self.loc_type}: newly infected person: {len(infected_neighbors)}"
                )
