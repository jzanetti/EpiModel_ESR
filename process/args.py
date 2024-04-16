from datetime import datetime


def args_preprocessing(
    seed_infection: str or None = None,
    infection_time: str or None = None,
    intital_timestep: str or None or None = None,
    dhb_list: str or None = None,
) -> tuple:
    """Arguments initial preprocessing

    Args:
        seed_infection (str): _description_
        infection_time (str): _description_
        intital_timestep (strorNone): _description_

    Returns:
        tuple: _description_
    """
    if seed_infection is not None and infection_time is not None:
        seed_infection_eval_list = eval(seed_infection)
        infection_time_eval_list = eval(infection_time)

        if not isinstance(seed_infection_eval_list, tuple):
            seed_infection = [seed_infection_eval_list]
            infection_time = [infection_time_eval_list]

    if intital_timestep is not None:
        intital_timestep = datetime.strptime(intital_timestep, "%Y%m%d")

    if dhb_list is not None:
        dhb_list = [s.replace("_", " ") for s in dhb_list]

    return {
        "seed_infection": seed_infection,
        "infection_time": infection_time,
        "intital_timestep": intital_timestep,
        "dhb_list": dhb_list,
    }


def obtain_args(parser):

    parser.add_argument(
        "--workdir",
        type=str,
        required=True,
        help="Working directory",
    )

    parser.add_argument(
        "--cfg",
        type=str,
        required=False,
        default=None,
        help="Configuration file",
    )

    parser.add_argument(
        "--model_id",
        type=str,
        required=True,
        help="Model ID",
    )

    parser.add_argument(
        "--create_model",
        action="store_true",
        help="Overwrite the model (e.g., recreating the person in the model)",
    )

    parser.add_argument(
        "--run_model",
        action="store_true",
        help="Run simulation",
    )

    parser.add_argument(
        "--run_vis",
        action="store_true",
        help="Run simulation visualization",
    )

    return parser
