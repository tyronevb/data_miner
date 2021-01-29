"""Script to run the Data Miner to parse raw, unstructured log files into a structured sequence of events."""

__author__ = "tyronevb"
__date__ = "2020"


import argparse
import sys

sys.path.append("..")
from src.data_miner import DataMiner  # noqa

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Data Miner to parse unstructured log files into a structured data set."
    )
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
        "log parsing method and tunable parameter values",
        required=True,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Display parsing details", dest="verbose")
    parser.add_argument(
        "-n", "--no_parameters", action="store_true", help="Don't save variable runtime parameters from log messages"
    )

    args = parser.parse_args()

    print("\n====================================")
    print("Running Data Miner . . .\n")

    # create data miner instance
    data_miner = DataMiner(config_file=args.config_file, input_dir=args.input_dir, output_dir=args.output_dir)

    print("Using parser: {}".format(data_miner.log_parser_method))
    print("With parameters: {}\n".format(data_miner.parameters))

    # parse logs
    data_miner.parse_logs(log_file=args.log_file, save_parameters=not args.no_parameters)

    print("====================================\n")
