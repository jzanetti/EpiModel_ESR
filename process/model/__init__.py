from enum import IntEnum


class Vaccine(IntEnum):
    NATURE = 3
    FULL = 2
    PARTIAL = 1
    NO = 0


class State(IntEnum):
    SUSCEPTIBLE = 0
    SEED_INFECTION = 1
    INFECTED = 2
    RECOVERED = 3
    INFECTED_NO_REPORT = 4
    REMOVED = 5
