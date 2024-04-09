def obtain_args(parser):

    parser.add_argument(
        "--workdir",
        type=str,
        required=False,
        default="/tmp/epimodel_esr",
        help="Working directory",
    )

    parser.add_argument(
        "--syspop_base_path",
        type=str,
        required=False,
        help="Synthetic population (base) data path",
    )

    parser.add_argument(
        "--syspop_diary_path",
        type=str,
        required=False,
        help="Synthetic population (diary) data path",
    )

    parser.add_argument(
        "--syspop_address_path",
        type=str,
        required=False,
        help="Synthetic population (address) data path",
    )

    parser.add_argument(
        "--syspop_healthcare_path",
        type=str,
        required=False,
        help="Synthetic population (healthcare) data path",
    )

    parser.add_argument(
        "--dhb_list",
        nargs="+",
        help="New Zealand DHB list",
        required=False,
        default=[],
    )

    parser.add_argument(
        "--sample_ratio",
        type=float,
        help="The percentage of interactions to be used",
        required=False,
        default=0.1,
    )

    parser.add_argument(
        "--seed_infection",
        type=int,
        help="The number of people being infected at the beginining",
        required=False,
        default=50,
    )

    parser.add_argument(
        "--infection_time",
        type=str,
        help="Infection time range in the format of '[start, end]'. For example, [0, 50]",
        required=False,
        default="[0, 50]",
    )

    parser.add_argument(
        "--overwrite_model",
        action="store_true",
        help="Overwrite the model (e.g., recreating the person in the model)",
    )

    return parser
