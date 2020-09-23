""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

import os
import sys
import yaml
import logging

from itertools import groupby

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

from pyrate.core.Run import Run


class Job:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level

    def setup(self):
        """Build global Job configuration and instantiate Run objects.
        The keys of the following dictionary will be distributed to the Run.
        """

        self.job = {"logger": None, "inputs": {}, "configs": {}, "outputs": {}}

        # --------------------------
        # Setup the logger
        # --------------------------

        self.job["logger"] = logging.getLogger("logger")
        self.job["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        for name, attr in self.config["inputs"].items():

            # This dictionary contains all input information. The file list contains lists
            # which can have more than one element in the case of multiple channels declared in the group.
            self.job["inputs"][name] = {"files": []}

            # Find all relevant files using the list of paths and filtering with the sample and channel tags.
            for f in FN.find_files(attr["path"]):
                self.job["inputs"][name]["files"].extend(
                    f
                    for s in ST.get_items(attr["samples"])
                    if s in ST.get_tags(f)
                    and FN.modus_ponens(
                        "group" in attr,
                        any(
                            c in ST.get_tags(f)
                            for c in ST.get_items(attr.get("group", False))
                        ),
                    )
                )

            # Group files using the first part of their names.
            self.job["inputs"][name]["files"] = [
                list(f)
                for j, f in groupby(
                    self.job["inputs"][name]["files"],
                    lambda a: a.partition("_")[0] if "group" in attr else None,
                )
            ]

            if not self.job["inputs"][name]["files"]:
                sys.exit(
                    f"ERROR: no input files found for input {name} under path {attr['path']}"
                )

            # Add all remaining attributes.
            self.job["inputs"][name].update(attr)

        self.job["configs"]["global"] = {"objects": {}}
        for name, attr in self.config["configs"].items():

            self.job["configs"][name] = {"files": []}

            for f in FN.find_files(attr["path"]):
                self.job["configs"][name]["files"].extend(
                    f
                    for n in ST.get_items(attr["names"])
                    if n in ST.get_tags(f) and f.lower().endswith(".yaml")
                )

            for f in self.job["configs"][name]["files"]:
                self.job["configs"][name].update(yaml.full_load(open(f, "r")))

            self.job["configs"]["global"]["objects"].update(
                self.job["configs"][name]["objects"]
            )

        for name, attr in self.config["outputs"].items():

            self.job["outputs"][name] = {"files": []}

            self.job["outputs"][name]["files"] = os.path.join(attr["path"], name)

            self.job["outputs"][name].update(attr)

        # -----------------------
        # Instantiate Run objects
        # -----------------------
        """ ToDo: find a criterion to split runs
        """
        self.runs = {}
        self.runs["test1"] = Run("test1", self.job)
        self.runs["test1"].setup()
        # self.runs["test2"] = Run("test2", self.job)
        # self.runs["test2"].setup()

    def launch(self):
        """Launch Run objects.
        ToDo: find a method to dispatch run objects.
        """

        sys.exit()

        """
        for name, attr in self.runs.items():
            attr.setup()
            attr.launch()
        """


# EOF
