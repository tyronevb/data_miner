"""
A script for tuning various log parsing methods implemented in LogParser.

Uses the ParserTuner class.
"""

__author__ = "tyronevb"
__date__ = "2020"

# TODO: fix relative imports

import sys

sys.path.append("../")
import argparse  # noqa
from src.parser_tuner import ParserTuner  # noqa

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tuning tool for tuning log parsing methods")
    parser.add_argument(
        "-l",
        "--log_file",
        action="store",
        type=str,
        help="Name of raw log file to be tuned on. Should not include path.",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input_dir",
        action="store",
        type=str,
        help="Absolute path to the input directory where the log file exists. Include trailing " "/",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        action="store",
        type=str,
        help="Absolute path to the output directory where the parsed logs and results of tuning "
        "are to be saved. Include trailing /",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--config_file",
        action="store",
        type=str,
        help="Path to configuration file (yaml) that contains "
        "the log format for the log files to be parsed, "
        "log parsing method and tunable parameter ranges",
        required=True,
    )
    parser.add_argument(
        "-g",
        "--ground_truth",
        action="store",
        type=str,
        help="Path to ground truth structured logs of the " "representative log file used for tuning",
        required=True,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Display tuning details", dest="verbose")
    parser.add_argument(
        "-n",
        "--new_config",
        action="store_true",
        help="Create a new config file for the log parser " "using the optimal tunable parameters",
        dest="new_config",
    )

    args = parser.parse_args()

    # create parser tuner object and initialise is with the config file
    parser_tuner = ParserTuner(config=args.config_file)

    # feed data to the parser tuner and tune the parser
    optimal_parameters = parser_tuner.tune_log_parser(
        input_log_file=args.log_file,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        ground_truth=args.ground_truth,
        verbose=args.verbose,
    )

    # create new data miner config file template (yaml) for the the log parser using the optimal parameters
    # only creates a bootstrap template that requires --> should be manually verified before using in data miner
    if args.new_config:
        parser_tuner.create_new_config_file(output_dir=args.output_dir)
