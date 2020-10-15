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
    def __init__(self, name, config, nevents, log_level):
        self.name = name
        self.config = config
        self.nevents = nevents
        self.log_level = log_level

    def setup(self):
        """Build global Job configuration and instantiate Run objects.
        The keys of the following dictionary will be distributed to the Run.
        """

        self.job = {"logger": None, "inputs": {}, "configs": {}, "outputs": {}}

        # --------------------------
        # Setup the logger
        # --------------------------

        self.job["logger"] = logging.getLogger("pyrate")
        self.job["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        for name, attr in self.config["inputs"].items():

            if self.nevents:
                attr["nevents"] = int(self.nevents)

            # This dictionary contains all input information. The file list contains lists
            # which can have more than one element in the case of multiple channels declared in the group.
            self.job["inputs"][name] = {"files": []}

            # Find all relevant files using the list of paths and filtering with the sample and channel tags.
            # Tags are looked for by separating underscores. If one file features multiple tags it will be
            # added multiple times here but duplicates will be removed at a later stage.
            # N.B the name of the tags required has to be exactly equal to the tag retrieved in the file for
            # this to be added in the list.
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
            # removing duplicates from the list of files. At this stage no groups are built yet.
            self.job["inputs"][name]["files"] = ST.remove_duplicates(
                self.job["inputs"][name]["files"]
            )
            print(self.job["inputs"][name]["files"])

            # Group files using the first tag found in their name.
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

        FN.pretty(self.job["inputs"])
        # -----------------------
        # Instantiate Run objects
        # -----------------------
        """ ToDo: find a criterion to split runs
        """

        #if self.nevents:

        self.runs = {}
        self.runs["test1"] = Run("test1", self.job)
        # self.runs["test1"].setup()
        # self.runs["test1"].launch()
        # self.runs["test2"] = Run("test2", self.job)
        # self.runs["test2"].setup()

    def launch(self):
        """Launch Run objects.
        ToDo: find a method to dispatch run objects.
        """
        for name, attr in self.runs.items():
            attr.setup()
            attr.launch()


# EOF
