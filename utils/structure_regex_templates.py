"""Utility for generating a more structured data set from manually created regex templates for log file parsing."""

__author__ = "tyronevb"
__date__ = "2020"

import argparse
import pandas as pd
import pathlib


def create_structured_regex_dataset(template_file: str):
    """
    Create a structured regex template data set.

    Takes a newline separated file containing regex templates for a set of log files and
    creates a structured template data set containing template ids and each regex template.

    Parameters
    ----------
    template_file: input template file containing newline separated regex for log message templates

    Returns
    -------
    output_file: path to newly generated output csv file
    """
    # get all regex templates from the file
    with open(template_file) as tf:
        templates = tf.readlines()

    template_dict = {}  # dictionary for storing mappings {ID:Template}

    # loop through each template, generate template id, append to dictionary
    for template_idx, template in enumerate(templates):
        template_dict["T{id}".format(id=template_idx + 1)] = template.strip()

    # create a pandas dataframe object from dictionary
    template_dataframe = pd.DataFrame(template_dict.items(), columns=["Template ID", "Template"])

    # output filename
    input_path = pathlib.Path(template_file)
    output_file = input_path.parent / (input_path.name.split(".")[0] + "_csv.csv")

    # save to csv
    template_dataframe.to_csv(output_file, index=False)

    return output_file


# if running as a script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tool for creating a structured data set from given regex templates. "
        "Creates and adds template ids to each of the regex given and "
        "creates a new template data set csv file."
    )
    parser.add_argument(
        "-i",
        "--input",
        action="store",
        required=True,
        help="Path to the file (.txt) containing regex for log message templates",
    )

    args = parser.parse_args()

    out_csv = create_structured_regex_dataset(args.input)

    print("Structured regex templates available at {}".format(out_csv))
