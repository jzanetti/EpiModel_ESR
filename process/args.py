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
        required=True,
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
        "--dhb_list",
        nargs="+",
        help="New Zealand DHB list",
        required=False,
        default=None,
    )

    parser.add_argument(
        "--sample_ratio",
        type=float,
        help="The percentage of interactions to be used",
        required=False,
        default=0.1,
    )

    parser.add_argument("--overwrite_model", action="store_true")

    return parser
