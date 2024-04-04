from enum import IntEnum
from random import sample as random_sample
from random import uniform as random_uniform

from mesa import Agent
from numpy.random import choice as numpy_choice

from process.model import CLINICAL_PARAMS
from process.model.weight import cal_infectiousness_profile
from process.utils import calculate_disease_days


class State(IntEnum):
    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2


class Vaccine(IntEnum):
    YES = 1
    NO = 0


class Agents(Agent):
    def __init__(
        self,
        unique_id,
        model,
        pos,
        loc_type,
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
        self.vaccine_status = numpy_choice([Vaccine.YES, Vaccine.NO], p=[0.9, 0.1])
        self.vaccine_efficiency = CLINICAL_PARAMS["vaccine_efficiency"]
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
            """
            setattr(
                self,
                f"infection_to_{days_type}_days",
                calculate_disease_days(
                    locals()[f"infection_to_{days_type}_days"], days_buffer
                ),
            )
            """

        self.infectiousness_profile = cal_infectiousness_profile(
            start_t=self.infection_to_infectiousness_days["start"],
            end_t=self.infection_to_infectiousness_days["end"],
            alpha=9.0,
            beta=0.5,
        )

    def step(self):
        if self.state == State.INFECTED:

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
            if (
                delta_t > self.infection_to_symptom_days["start"]
                or delta_t < self.infection_to_symptom_days["end"]
            ):
                if numpy_choice([True, False], p=[0.75, 0.25]):
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
            for neighbor in neighbors:
                # if neighbor.unique_id == 496996:
                if neighbor.unique_id == self.unique_id:
                    continue

                if neighbor.state == State.SUSCEPTIBLE:
                    if neighbor.vaccine_status == Vaccine.NO:
                        neighbor.state = State.INFECTED
                        neighbor.infection_time = self.model.timestep
                    else:
                        if numpy_choice(
                            [True, False],
                            p=[1.0 - self.vaccine_efficiency, self.vaccine_efficiency],
                        ):
                            self.state = State.INFECTED
                            self.infection_time = self.model.timestep
