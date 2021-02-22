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

        self.job = {
            "no_progress_bar": self.config["no_progress_bar"],
            "logger": None,
            "inputs": {},
            "configs": {},
            "outputs": {},
        }

        # --------------------------
        # Setup the logger
        # --------------------------

        self.job["logger"] = logging.getLogger("pyrate")
        self.job["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        for name, attr in self.config["inputs"].items():

            # This dictionary contains all input information. The file list contains lists
            # which can have more than one element in the case of multiple channels declared in the group.
            self.job["inputs"][name] = {"files": []}

            # Files are collected looking for tags separated by underscores. Sevaral options are available
            # to collect tags.
            # 1) any: (REQUIRED) collect a file if it contains any of these tags.
            # 2) all: collect a file if it contains all of these tags.
            # 3) gropus: if a file starts with any of the tags declared here it will be considered as part of a group.
            for f in FN.find_files(attr["path"]):
                self.job["inputs"][name]["files"].extend(
                    f
                    for s in ST.get_items(attr["samples"]["tags"]["any"])
                    if s in ST.get_tags(f)
                    and FN.modus_ponens(
                        "all" in attr["samples"]["tags"],
                        all(
                            t in ST.get_tags(f)
                            for t in ST.get_items(
                                attr["samples"]["tags"].get("all", False)
                            )
                        ),
                    )
                    and FN.modus_ponens(
                        "groups" in attr["samples"]["tags"],
                        any(
                            c in ST.get_tags(f)
                            for c in ST.get_items(
                                attr["samples"]["tags"].get("groups", False)
                            )
                        ),
                    )
                )
            # removing duplicates from the list of files. At this stage no groups are built yet.
            self.job["inputs"][name]["files"] = ST.remove_duplicates(
                self.job["inputs"][name]["files"]
            )

            # Group files using the first tag found in their name.
            self.job["inputs"][name]["files"] = [
                list(f)
                for j, f in groupby(
                    self.job["inputs"][name]["files"],
                    lambda a: a.partition("_")[0]
                    if "groups" in attr["samples"]["tags"]
                    else None,
                )
            ]

            if not self.job["inputs"][name]["files"]:
                sys.exit(
                    f"ERROR: no input files found for input {name} under path {attr['path']}"
                )

            # Add all remaining attributes.
            self.job["inputs"][name].update(attr)

        print(self.job["inputs"])

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

            for obj in attr["objects"]:
                for o_name, o_attr in obj.items():

                    if o_attr == "all":
                        samples = ST.remove_duplicates(self.job["inputs"])
                    else:
                        samples = ST.get_items(obj[o_name])

                    samples.sort()

                    s_names = ",".join(samples)

                obj[o_name] = samples

                obj[":".join([o_name, s_names])] = obj.pop(o_name)

            self.job["outputs"][name].update(attr)

        # -----------------------
        # Instantiate Run object
        # -----------------------
        self.run = Run(f"{self.name}_run", self.job)

        self.run.setup()

    def launch(self):
        """Launch Run objects. """
        self.run.launch()


# EOF
