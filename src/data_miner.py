"""
Implements the DataMiner class.

An instance of DataMiner is initialised to use a specified log parsing method. Data, i.e. raw log files,
are then passed to the DataMiner to invoke the parse_logs() method to parse the log files into
a structured sequence of events and event templates.
"""

__author__ = "tyronevb"
__date__ = "2020"

import yaml
import pandas as pd
import sys

sys.path.append("..")
from logparser.logparser import Drain, Spell, AEL, IPLoM, LenMa, LogMine  # noqa
from logparser.logparser.utils import evaluator  # noqa
from src import RegexLogParser  # noqa
from typing import Tuple, List  # noqa


class DataMiner(object):
    """Class definition for the DataMiner class."""

    def __init__(self, config_file: str, input_dir: str, output_dir: str, verbose: bool = False):
        """
        Initialise DataMiner.

        The DataMiner is initialised with the log parsing method,
        and various configuration options from the specified configuration file.
        Parameters
        ----------
        config_file: path to config file specifying options for the data miner (.yaml file)
        input_dir: path to directory where the log files to be analysed are located. should include trailing /
        output_dir: path to directory where generated structured log files are to be saved. should include trailing /
        verbose: flag to enable printing of various runtime process information
        """
        # set verbose flag
        self.verbose = verbose

        # dictionary mapping parser names to classes
        self.methods = {
            "drain": Drain,
            "spell": Spell,
            "iplom": IPLoM,
            "lenma": LenMa,
            "logmine": LogMine,
            "ael": AEL,
            "regex": RegexLogParser,
        }

        # parse config file for data miner configuration
        self.log_format, self.preprocess_regex, self.log_parser_method, self.parameters = self.parse_config_file(
            config_file=config_file, debug=self.verbose
        )

        # instantiate and configure log parser based on config file settings
        self.log_parser = self.methods[self.log_parser_method].LogParser(
            log_format=self.log_format, indir=input_dir, outdir=output_dir, rex=self.preprocess_regex, **self.parameters
        )

    # @profile uncomment to profile memory usage
    def parse_logs(self, log_file: str, save_parameters=True) -> (str, str):
        """
        Parse the given log files.

        Invoke the DataMiner's log parser to parse the given log files into a data set of sequenced events and
        event templates.
        Parameters
        ----------
        log_file: filename of raw log file to be parsed (just filename, no path)
        save_parameters: flag to enable extracting and saving of runtime variable parameters in log messages
        """
        # check flag for saving runtime parameters
        if save_parameters:
            self.log_parser.keep_para = True  # set attribute flag in LogParser to save parameters
        else:
            self.log_parser.keep_para = False  # set attribute flag in LogParser to not save parameters

        self.log_parser.parse(log_file)

        path_to_event_matrix = self.log_parser.savePath + log_file + "_templates.csv"
        path_to_structured_log = self.log_parser.savePath + log_file + "_structured.csv"

        return path_to_structured_log, path_to_event_matrix

    @staticmethod
    def parse_config_file(config_file: str, debug: bool = False) -> Tuple[str, List[str], str, dict]:
        """
        Parse config file.

        Parse the specified configuration file to retrieve parser configuration.

        Parameters
        ----------
        config_file: yaml config file containing configuration information for
        data miner log parser tuning
        debug: optional flag to enable printing out the parsed configuration

        Returns
        -------
        log_format: log message format (for extracting content from header)
        preprocess_regex: pre-processing regex for the log files
        log_parser: log parsing method to be used/tuned
        parameters: tunable parameters for the log parsing method
        """
        # load config file for parameter tuning
        with open(config_file) as config:
            data = yaml.load(config, Loader=yaml.FullLoader)

        # identify the parser from the config file
        logparser = data["logparser"]["method"]  # parser is a string (name) of the log parsing method

        # extract the paramter settings from the config file
        parameters = data["logparser"]["parameters"]

        # extract preprocessing regular expressions and convert to raw string
        preprocess_regex = []
        for regex in data["preprocess"]:
            if regex is None:
                pass
            else:
                preprocess_regex.append(r"{}".format(regex.strip()))

        # extract log message format (log header/preamble)
        log_format = data["log_format"]

        if debug:
            print("\nConfiguration parsed from config file:\n=====================================")
            print(
                "log_format: {lf}\npreprocess_regex: {pr}\nlogparser: {lp}\nparameters: {p}\n".format(
                    lf=log_format, pr=preprocess_regex, lp=logparser, p=parameters
                )
            )

        return log_format, preprocess_regex, logparser, parameters

    @staticmethod
    def inspect_parsed_result(parsed_log: str) -> Tuple[int, int]:
        """
        Inspect the parsed log file and get stats.

        :param parsed_log: path to the parsed log file
        :return: (int, int) - number of log messages parsed, number of unique events
        """
        df_parsed_log = pd.read_csv(parsed_log)

        num_log_messages = len(df_parsed_log)

        num_unique_events = df_parsed_log["EventId"].nunique()

        return num_log_messages, num_unique_events


# end
