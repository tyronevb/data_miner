"""Script to run the Data Miner to parse raw, unstructured log files into a structured sequence of events."""

__author__ = "tyronevb"
__date__ = "2020"


import argparse
from datetime import datetime
import os
import sys


sys.path.append("..")
sys.path.append("../")
from src.data_miner import DataMiner  # noqa
from logparser.logparser.utils import evaluator  # noqa

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
    parser.add_argument(
        "-n", "--no_parameters", action="store_true", help="Don't save variable runtime parameters from log messages"
    )
    parser.add_argument(
        "-e",
        "--evaluate",
        action="store",
        help="Evaluate the performance of the Data Miner. Requires"
        "ground truth dataset to be provided. Provide as absolute path to ground truth csv.",
        default=None,
    )

    args = parser.parse_args()

    log_f = list()

    log_f.append("\n====================================")
    log_f.append("Running Data Miner . . .\n")

    print("\n====================================")
    print("Running Data Miner . . .\n")

    # create data miner instance
    data_miner = DataMiner(config_file=args.config_file, input_dir=args.input_dir, output_dir=args.output_dir)

    log_f.append("Using parser: {}".format(data_miner.log_parser_method))
    log_f.append("With parameters: {}\n".format(data_miner.parameters))

    print("Using parser: {}".format(data_miner.log_parser_method))
    print("With parameters: {}\n".format(data_miner.parameters))

    # parse logs
    start_t = datetime.now()
    path_to_structured_log, path_to_event_matrix = data_miner.parse_logs(
        log_file=args.log_file, save_parameters=not args.no_parameters
    )
    end_t = datetime.now()
    log_all = list()
    log_all.append("\nParsed log available at: {p_logfile}\n".format(p_logfile=path_to_structured_log))

    num_logs, num_events = data_miner.inspect_parsed_result(path_to_structured_log)

    log_all.append("\nNumber of log messages parsed: {}".format(num_logs))
    log_all.append("Number of unique log events extracted: {}\n".format(num_events))

    # evaluate Data Miner Performance
    if args.evaluate:
        # measure the f1_measure and accuracy --> using the ground truth
        f1_measure, accuracy, precision, recall = evaluator.evaluate(
            groundtruth=args.evaluate,
            parsedresult=os.path.join(args.output_dir, args.log_file + "_structured.csv"),
        )
        log_all.append("Data Miner Performance Evaluation:")
        log_all.append("Time taken to parse: {}".format((end_t - start_t).total_seconds()))
        log_all.append(
            "Precision: {precision:.4f}\nRecall: {recall:.4f}\n"
            "F1 Measure: {f_measure:.4f}\nAccuracy: {accuracy:.4f}".format(
                precision=precision,
                recall=recall,
                f_measure=f1_measure,
                accuracy=accuracy,
            )
        )
    log_all.append("====================================")

    with open(
        "{output_dir}/{name}".format(
            output_dir=args.output_dir, name="data_miner_run_" + datetime.now().strftime("%m-%d-%Y_%Hh%Mm%Ss") + ".txt"
        ),
        "w",
    ) as f:
        for log in log_f:
            f.write(log + "\n")
        for log in log_all:
            print(log)
            f.write(log + "\n")

# end
