SA2_DATA_PATH = "etc/dhb_and_sa2.parquet"
SAVED_MODEL_PATH = "{workdir}/model.dill"


CLINICAL_PARAMS = {
    "reproduction_rate": 12.0,
    "infection_to_incubation_days": {"start": 0, "end": 10},
    "infection_to_infectiousness_days": {"start": 10, "end": 21},
    "infection_to_symptom_days": {"start": 11, "end": 20},
    "infection_to_recovered_days": 21,
    "vaccine_efficiency": 0.95,
}

MEASURES = {"stay_at_home_if_symptom": {"enable": True, "percentage": 0.8}}


TOTAL_TIMESTEPS = 180

VIS_COLOR = {0: "red", 1: "green", 2: "blue"}
