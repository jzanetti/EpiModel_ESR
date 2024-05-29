from datetime import datetime


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
        required=False,
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

    parser.add_argument(
        "--run_ens",
        action="store_true",
        help="Run ens visualization",
    )

    return parser
