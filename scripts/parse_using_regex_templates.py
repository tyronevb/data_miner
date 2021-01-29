"""Utility for parsing log files using manually created Regex-based Event Templates."""

__author__ = "tyronevb"
__date__ = "2020"

import argparse
import sys
import yaml

sys.path.append("..")
from src import RegexLogParser  # noqa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse a raw log file into a structured data set using Regex-based Event Templates"
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
        help="Absolute path to the input directory where the log file exists. Include trailing" "/",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        action="store",
        type=str,
        help="Absolute path to the output directory where the parsed logs and results of tuning"
        "are to be saved. Include trailing /",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--config_file",
        action="store",
        type=str,
        help="Path to configuration file (yaml) that contains"
        "the log format for the log files to be parsed,"
        "log parsing method and tunable parameter values",
        required=True,
    )
    parser.add_argument("-p", "--print_stats", action="store_true", help="Display parsing stats", dest="print_stats")
    parser.add_argument(
        "-u",
        "--save_unparsed",
        action="store_true",
        help="Save un-parsed log messages to a file",
        dest="save_un_parsed",
    )
    parser.add_argument(
        "-k",
        "--keep_parameters",
        action="store_true",
        help="Extract and save variable parameters for each log" "message",
    )

    args = parser.parse_args()

    # parse config file here
    with open(args.config_file, "r") as config:
        data = yaml.load(config, Loader=yaml.FullLoader)

    # extract log message format (log header/preamble)
    log_format = data["log_format"]

    # extract the paramter settings from the config file
    parameters = data["logparser"]["parameters"]

    # extract preprocessing regular expressions and convert to raw string
    preprocess_regex = []
    for regex in data["preprocess"]:
        if regex is None:
            pass
        else:
            preprocess_regex.append(r"{}".format(regex.strip()))

    # create the log parser object
    log_parser = RegexLogParser.LogParser(
        log_format=log_format,
        indir=args.input_dir,
        outdir=args.output_dir,
        rex=preprocess_regex,
        save_un_parsed=args.save_un_parsed,
        keep_para=args.keep_parameters,
        **parameters
    )

    # parse the logs
    log_parser.parse(logName=args.log_file)

    print("===================================================")
    print("Parsing using ground truth rules/templates complete.")
    print("\nStructured log file available in {output}".format(output=args.output_dir))

    if args.print_stats:
        num_parsed = len(log_parser.df_parsed)
        num_un_parsed = len(log_parser.df_un_parsed)
        print(
            "\nStats:\nTime Taken (s): {e_time}\n"
            "# Log Messages Parsed: {parsed}\n"
            "# Log Messages Un-parsed: {un_parsed}".format(
                e_time=log_parser.time_to_parse, parsed=num_parsed, un_parsed=num_un_parsed
            )
        )
    print("\n===================================================")
