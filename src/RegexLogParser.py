"""
Defines a class that implements a LogParser based on manually created regular expressions.

Has the same interface as the other methods in the LogParser toolkit.

RegexLogParser

This log parser parses log files into a structured sequence of events. Log messages are parsed
using defined regular expressions that define the various log message templates or event templates
for the log file in question. Messages are replaced by an event template and a set of runtime
parameters associated with the log message.
"""

__author__ = "tyronevb"
__date__ = "2020"

import pandas as pd
import re
import os
from datetime import datetime


class LogParser(object):
    """Class definition for LogParser."""

    def __init__(
        self,
        log_format: str,
        indir: str = "./",
        outdir: str = "./result/",
        rex: list = [],
        regex_templates: str = None,
        save_un_parsed: bool = False,
        keep_para: bool = True,
    ):
        """
        Init constructor.

        Parameters
        ----------
        log_format: format of the log messages (for extracting header and content)
        indir: path to input director where log files are located, to include trailing /
        outdir: path to output directory where parsed log files are to be saved
        rex: pre-processing regex for the log messages
        regex_templates: path to .csv file containing regex event templates
        save_un_parsed: flag to enable saving un-parsed messages to a separate file
        keep_para: flag to enable extracting and saving of runtime parameters
        """
        self.path = indir
        self.save_path = outdir
        self.log_format = log_format
        self.rex = rex
        self.keep_para = keep_para
        self.save_un_parsed = save_un_parsed
        self.regex_templates = regex_templates

        # attribute definitions
        self.headers = None
        self.regex = None
        self.log_file = None
        self.df_log = None
        self.df_parsed = None
        self.df_un_parsed = None
        self.time_to_parse = None

    def generate_logformat_regex(self) -> (list, re.Pattern):
        """
        Generate regular expression to split log messages.

        This function generates a regular expression to split log messages based on the log format
        provided. The various components of the log message are used as headings for a data
        structure that contains all the components of the log messages.

        Adapted from logparser (https://github.com/logpai/logparser)

        Licence: MIT

        Returns
        -------
        headers: names for the various components of the log messages
        regex: regular expression for extracting various components of the log message
        """
        headers = []  # store the extracted header of a component of the message
        splitters = re.split(r"(<[^<>]+>)", self.log_format)  # split the given log format into groups
        # note: this relies on the presence of <> to denote the group names of the components
        # () --> used to capture text of all groups, captures delimiters, and create group
        # < --> match '<'
        # [^..] --> set of characters to match excluding the given characters
        # + --> match 1 or more (the or more is the important part here) of the preceeding RE i.e. [^<>]
        # > --> match '>'

        regex = ""  # define an empty string to use to build the regular expression

        # loop over the indices of the groups generated by the split above
        for k in range(len(splitters)):
            # for every even index
            if k % 2 == 0:
                # look for whitespace and replace with the re for whitespace
                splitter = re.sub("\s+", "\\\s+", splitters[k])  # noqa
                regex += splitter  # add to the regular expressions
            # for every odd index
            else:
                # this is expected to be a header, based on how the groups are split above
                header = splitters[k].strip("<").strip(">")  # strip away the enclosing '<' and '>' characters
                regex += "(?P<%s>.*?)" % header  # ?P<name> --> named group, .*? --> match as few characters as possible
                headers.append(header)
        regex = re.compile("^" + regex + "$")  # compile into a regex that can be used for matching etc.
        return headers, regex  # return the headers and regex

    def log_to_dataframe(self, log_file: str, regex: re.Pattern, headers: list) -> pd.DataFrame:
        """
        Transform log file to DataFrame.

        Adapted from logparser (https://github.com/logpai/logparser)

        Licence: MIT

        Parameters
        ----------
        log_file: file name of the log file to be parsed (just file name, not path)
        regex: regular expression for extracting components of the log message
        headers: list of names for the various components of the log messages

        Returns
        -------
        logdf: dataframe of the log file with each log message split into its components
        (rows = log messages, columns = message components)
        """
        log_messages = []
        linecount = 0
        with open(os.path.join(self.path, log_file), "r") as fin:
            for line in fin.readlines():  # for each log message
                try:
                    match = regex.search(line.strip())  # match the log format specific
                    message = [match.group(header) for header in headers]  # isolate each group
                    log_messages.append(message)  # append to list of log messages
                    linecount += 1  # increment line count
                except Exception as e:  # noqa
                    pass  # if a match is not found, skip
        logdf = pd.DataFrame(log_messages, columns=headers)  # convert to a pandas DataFrame
        logdf.insert(0, "LineId", None)  # create a new column/attribute for LineId
        logdf["LineId"] = [i + 1 for i in range(linecount)]  # populate the LineId field
        return logdf  # return the data frame

    def parse(self, logName: str):
        """
        Parse a given log file into a series of structured events.

        Outputs a structured log file and a count of event occurrences.
        Parameters
        ----------
        logName: name of the log file to be parsed (just filename, no path)
        """
        print("\nParsing file: {}".format(os.path.join(self.path, logName)))
        start_time = datetime.now()
        self.log_file = logName

        # parse log based on message structure and load the log file into a pandas dataframe
        self.headers, self.regex = self.generate_logformat_regex()

        df_log_file = self.log_to_dataframe(log_file=self.log_file, regex=self.regex, headers=self.headers)

        # load the regex event templates
        df_regex_templates = pd.read_csv(self.regex_templates)

        # create a copy of the incoming dataframe because we want to modify it (deep=True --> deep copy)
        df_un_parsed = df_log_file.copy(deep=True)
        df_parsed = df_log_file.copy(deep=True)

        labels = ("Event ID", "Event Template")
        events = []
        templates = []
        template_ids = []
        parameters = []

        # need to loop over log messages first to preserve the order of the messages
        count = 0
        for idx, message in df_un_parsed.iterrows():
            for idx2, template_row in df_regex_templates.iterrows():
                # raw strings are used for regex to account for characters like \
                # note to strip both the message and template to remove '\n' (newlines)
                # note: need to manually re-create raw string here after reading from file
                # check if the a log message matches the current template
                # storing the output of re.fullmatch gives access to the matched groups i.e. the variable parameters
                template_match = re.fullmatch(
                    r"{}".format(template_row["Template"].strip()), message["Content"].strip()
                )

                if template_match:
                    entry = (template_row["Template ID"], template_row["Template"].strip())

                    # append to the parsed events tuple
                    events.append(entry)
                    templates.append(template_row["Template"])
                    template_ids.append(template_row["Template ID"])

                    temp_param_list = []
                    # apply some post-processing to extract parameters
                    for param in template_match.groups():
                        unique_params = param.split(",")
                        for u in unique_params:
                            temp_param_list.append(u.strip().replace("'", ""))
                    parameters.append(temp_param_list)

                    # drop log message from the copied dataset (reduces the search space after each iteration)
                    # also keeps a record of entries that are unmatched
                    df_un_parsed.drop(idx, inplace=True)
                    break  # include a break here so that a message is only considered until a match is found
                else:
                    # no match
                    pass

            count += 1
            if count % 1000 == 0 or count == len(df_log_file):
                print("Processed {0:.1f}% of log lines.".format(count * 100.0 / len(df_log_file)))

        # drop all unmatched messages from the df_parsed DataFrame
        df_parsed.drop(df_un_parsed.index, inplace=True)

        # create structured DataFrame of all matched log messages
        df_parsed["Event ID"] = template_ids
        df_parsed["Event Template"] = templates
        if self.keep_para:
            df_parsed["Parameters"] = parameters

        self.time_to_parse = datetime.now() - start_time
        print("Parsing done. [Time taken: {!s}]".format(self.time_to_parse))

        # create DataFrame of event templates and occurrences
        df_events = pd.DataFrame.from_records(events, columns=labels)
        df_events["Occurrences"] = df_events.groupby(["Event ID"])["Event Template"].transform("count")
        df_events.drop_duplicates(inplace=True)

        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        # create csv outputs of all files
        structured_log_output = os.path.join(self.save_path, self.log_file + "_structured.csv")
        event_template_output = os.path.join(self.save_path, self.log_file + "_templates.csv")

        df_parsed.to_csv(structured_log_output, index=False)
        df_events.to_csv(event_template_output, index=False)

        if self.save_un_parsed:
            # save the unmatched logs to a file
            unmatched_messages_output = os.path.join(self.save_path, self.log_file + "_unmatched.csv")
            df_un_parsed.to_csv(unmatched_messages_output, index=False)

        self.df_parsed = df_parsed
        self.df_un_parsed = df_un_parsed
