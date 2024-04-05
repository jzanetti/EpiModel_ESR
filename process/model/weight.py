from numpy import linspace as numpy_linspace
from scipy.stats import gamma as scipy_gamma

from process import CLINICAL_PARAMS


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
