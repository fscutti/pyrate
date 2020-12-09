""" This class is dedicated to the creation of job configuration files,
and their submission spawning from one original job configuration file.
"""

import os
import sys
import yaml
import logging
import itertools

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Scheduler:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level

    def setup(self):

        self.sets = {"logger": None, "batches": {}, "jobs": {}}

        # --------------------------
        # Setup the logger
        # --------------------------

        self.sets["logger"] = logging.getLogger("spyrate")
        self.sets["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        for name, attr in self.config["jobs"].items():

            self.sets["jobs"][name] = {}

            for f in FN.find_files(attr["path"]):
                if f.endswith(name + ".yaml"):

                    self.sets["jobs"][name].update(yaml.full_load(open(f, "r")))
                    self.sets["jobs"][name].update(attr)

                    break

        # create batch jobs dictionary
        """
        for jname, jattr in self.sets["jobs"].items():
            for fname, fattr in jattr["factorisation"].items():

                maintain_original = {"inputs": True, "outputs": True}

                if fname == "inputs":
                    for i in fattr:
                        if i in jattr["inputs"]:
                            self.sets["batches"]
        """

        for jname, jattr in self.sets["jobs"].items():

            self.sets["batches"][jname] = {}

            # modify event slices
            if "eparts" in jattr["factorisation"]:

                ep = jattr["factorisation"]["eparts"]

                jattr["factorisation"]["eparts"] = [
                    f"slice_{s+1}_nparts_{ep}" for s in range(ep)
                ]

            for tags in list(itertools.product(*list(jattr["factorisation"].values()))):

                bname = "_".join([f"{t}" for t in tags])

                self.sets["batches"][jname][bname] = {}

        print(self.sets["batches"])

    def launch(self):
        pass

    def _write_script(self):
        pass


# EOF
