"""
Implements the ParserTuner class.

Grid-search based tuning for finding optimal tunable parameters for various
log parsing methods/techniques. Tunes log parsing methods as implemented by
logparser (https://github.com/logpai/logparser)
"""

__author__ = "tyronevb"
__date__ = "2020"

import time
import os
import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import ParameterGrid
import sys

sys.path.append("../")
from logparser.logparser import Drain, Spell, AEL, IPLoM, LenMa, LogMine  # noqa
from logparser.logparser.utils import evaluator  # noqa
from typing import Tuple, List  # noqa


class ParserTuner(object):
    """Class definition for ParserTuner."""

    def __init__(self, config: str):
        """
        Object initialisation.

        Parameters
        ----------
        config: absolute path to configuration file for tuning
        """
        # dictionary mapping parser names to classes
        self.log_parsers = {
            "drain": Drain,
            "spell": Spell,
            "iplom": IPLoM,
            "lenma": LenMa,
            "logmine": LogMine,
            "ael": AEL,
        }

        # extract configuration from config file
        self.log_format, self.preprocess_regex, self.logparser, self.parameters = self.parse_config_file(config)

        # create ParameterGrid object from parameter search space
        self.parameter_grid = self.create_parameter_grid(self.parameters)

        # initialise attribute to store optimal parameter configuration
        self.optimal_parameters = None

    @staticmethod
    def create_parameter_grid(parameter_ranges: dict) -> ParameterGrid:
        """
        Create Parameter Grid for grid search.

        Create a ParameterGrid from the ranges of values for the tunable parameters
        Parameters
        ----------
        parameter_ranges: nested dictionary containing ranges for tunable parameters
        {"parameter_1": {"min": value, "max": value, "step": value},
         "parameter_2": ..., }

        Returns
        -------
        ParameterGrid: a ParameterGrid interable object for the tunable parameter search space
        """
        # create empty dictionary to store parameters and value ranges
        parameter_dict = {}

        # populate the paramter_dict by generating allowable ranges for each parameter
        # note to include max, add the step size to it (upper bound is exclusive in np.arange)
        for key, value in parameter_ranges.items():
            parameter_dict[key] = np.arange(value["min"], value["max"] + value["step"], value["step"])

        # create and return the ParameterGrid object
        return ParameterGrid(parameter_dict)

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
                "log_format: {lf}\npreprocess_regex: {pr}\nlogparser: {lp}\nparameters: {p}".format(
                    lf=log_format, pr=preprocess_regex, lp=logparser, p=parameters
                )
            )

        return log_format, preprocess_regex, logparser, parameters

    def tune_log_parser(
        self, input_log_file: str, input_dir: str, output_dir: str, ground_truth: str, verbose: bool = False
    ) -> dict:
        """
        Find the optimal set of tunable parameters for a given log parsing method.

        Requires an already parsed/structured version of the log file to be used as a ground truth
        for evaluation.
        Parameters
        ----------
        input_log_file: filename, not path, of the log file to be used for tuning
        input_dir: path to where the input log file is located, should include trailing /
        output_dir: path to where results of tuning should be saved, should include trailing /
        ground_truth: path to ground truth dataset corresponding to the input log file
        verbose: flag to enable printing of tuning stats

        Returns
        -------
        optimal_parameters: the set of optimal parameters for the log parser as found by tuning
        """
        # determine the total number of combinations
        total_combinations = len(self.parameter_grid)

        start_t = time.time()
        results = []
        tuning_record = []
        # use the parameter space to determine the optimal set
        for idx, combination in enumerate(self.parameter_grid):
            # for every combination of parameters...

            # create new output dirs for each idx
            current_output_dir = "{base_dir}run_{idx}/".format(base_dir=output_dir, idx=idx)

            # define a new log parser with the set of tunable parameters
            l_parser = self.log_parsers[self.logparser].LogParser(
                log_format=self.log_format,
                indir=input_dir,
                outdir=current_output_dir,
                rex=self.preprocess_regex,
                **combination
            )

            if verbose:
                print("Considering parameter set {}: {}".format(idx, combination))

            # parse the raw log file using the initialised parser
            l_parser.parse(input_log_file)

            # measure the f1_measure and accuracy --> using the ground truth
            f1_measure, accuracy = evaluator.evaluate(
                groundtruth=ground_truth,
                parsedresult=os.path.join(current_output_dir, input_log_file + "_structured.csv"),
            )

            # append the accuracy acheived for this set of paramters to a list
            results.append(accuracy)
            # create new list of results + parameter set
            tuning_record.append([idx, combination, accuracy])

        # after exploring the entire parameter search space...
        # find combination of parameters that optimize the objective function
        # need to find the maximum value and the index of it
        # python lists are ordered and maintains persistent order
        optimal_combo_idx = np.argmax(results)  # find the index of the max accuracy

        # find the set of parameters that yielded the max accuracy
        self.optimal_parameters = self.parameter_grid[optimal_combo_idx]

        df_tuning_record = pd.DataFrame(tuning_record, columns=["Run", "Parameter Set", "Accuracy"])
        df_tuning_record.set_index("Run", inplace=True)

        tuning_file_name = "tuning_record_{date}.csv".format(date=time.strftime("%m-%d-%Y_%Hh%Mm%Ss"))

        df_tuning_record.to_csv("{output_dir}{filename}".format(output_dir=output_dir, filename=tuning_file_name))

        end_t = time.time()
        print("\n==========================")
        print("Logparser tuning complete!")

        # print out the optimal parameters
        print(
            "\nOptimal combination of parameters for "
            "{logparser}: {optimal}".format(logparser=self.logparser, optimal=self.optimal_parameters)
        )

        # print stats and results
        if verbose:
            print("\nNumber of combinations for tunable parameters: {combos}".format(combos=total_combinations))
            print("Time taken to search entire parameter space: {tune_time} seconds".format(tune_time=end_t - start_t))
            print("Tuning record available at {filename}".format(filename=tuning_file_name))

        print("\n==========================")

        return self.optimal_parameters

    def create_new_config_file(self, output_dir: str):
        """
        Create new configuration file with optimal parameter values.

        Create a new template configuration file (.yaml) to be used with the data miner
        for parsing logs of the same format as was used during tuning.

        This creates a boilerplate config file that should be inspected manually.
        Parameters
        ----------
        output_dir: path to directory where the new config file should be saved.
        should include trailing /
        """
        output_file_name = "{outdir}data_miner_config_{method}_{date}.yaml".format(
            outdir=output_dir, method=self.logparser, date=time.strftime("%m-%d-%Y_%Hh%Mm%Ss")
        )
        config = dict()
        config["log_format"] = self.log_format
        config["preprocess"] = self.preprocess_regex
        lp = dict()
        lp["method"] = self.logparser
        lp["parameters"] = self.optimal_parameters
        config["logparser"] = lp

        # the parameters are numpy objects, just extract the value here
        # otherwise yaml.dump will dump the object to the .yaml file
        for key, value in lp["parameters"].items():
            lp["parameters"][key] = float(value)

        with open(output_file_name, "w") as f:
            _ = yaml.dump(config, f)

        print("\nNew template config file created: {config_temp}".format(config_temp=output_file_name))
