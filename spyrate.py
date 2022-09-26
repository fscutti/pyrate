#!/usr/bin/env python3

import os
import argparse
import yaml

from pyrate.core.Batch import Batch

parser = argparse.ArgumentParser(description="Command line options for pyrate")

# -------------------------------------------------------------------
# Some comment.
# -------------------------------------------------------------------
parser.add_argument(
    "--batch_config",
    "-b",
    help="batch jobs configuration file",
    required=True,
)

parser.add_argument(
    "--logging_level",
    "-l",
    help="logging level",
    required=False,
    default="CRITICAL",
)

args = parser.parse_args()

if __name__ == "__main__":

    b_file = args.batch_config

    b_name = b_file.split("/")[-1].split(".")[0]

    b_config = yaml.full_load(open(b_file, "r"))

    b_log = args.logging_level

    batch = Batch(b_name, b_config, b_log)

    batch.setup()

    batch.launch()

# EOF
