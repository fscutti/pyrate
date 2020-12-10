""" This class is dedicated to the creation of job configuration files,
and their submission spawning from one original job configuration file.
"""

import os
import sys
import yaml
import copy
import logging
import itertools
import shutil

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

        # create original job dictionary
        for name, attr in self.config["jobs"].items():

            self.sets["jobs"][name] = {}

            for f in FN.find_files(attr["path"]):
                if f.endswith(name + ".yaml"):

                    self.sets["jobs"][name].update(yaml.full_load(open(f, "r")))
                    self.sets["jobs"][name].update(attr)

                    break

        # create batch jobs dictionary
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

        # transfer fields from original job dictionaries to the batch one.
        for jname, bnames in self.sets["batches"].items():
            for bname in bnames:

                # if fields are specified in the factorisation
                # modify the settings of the original job field.
                if "eparts" in self.sets["jobs"][jname]["factorisation"]:
                    eparts = bname.split("slice", 1)[1].split("_")

                    for iname, iattr in self.sets["jobs"][jname]["inputs"].items():

                        b_slice, b_nparts = eparts[1], eparts[3]

                        # N.B.: this is iteratively modifying an attribute
                        # of the original job. Later on this would need to be
                        # copied when building the corresponding attribute of
                        # the batch job.
                        iattr["eslices"] = {"slice": b_slice, "nparts": b_nparts}

                self._prepare_field(jname, bname, "inputs")
                self._prepare_field(jname, bname, "outputs")

                # add remaining fields from the original job config file which
                # were not scheduled for modifiction.
                for field in ["inputs", "configs", "outputs"]:
                    if field in self.sets["batches"][jname][bname]:
                        continue
                    else:
                        self.sets["batches"][jname][bname].update(
                            {field: self.sets["jobs"][jname][field]}
                        )

        self._prepare_directories()

    def launch(self):
        pass

    def _prepare_field(self, job_name, batch_name, field):
        """Prepare the inputs/outputs field of the batch job."""

        if field in self.sets["jobs"][job_name]["factorisation"]:
            for f in self.sets["jobs"][job_name]["factorisation"][field]:

                if f in batch_name:

                    modf = f

                    if field == "outputs":
                        modf = batch_name

                    try:
                        self.sets["batches"][job_name][batch_name][field].update(
                            {modf: copy.copy(self.sets["jobs"][job_name][field][f])}
                        )

                    except KeyError:
                        self.sets["batches"][job_name][batch_name].update(
                            {
                                field: {
                                    modf: copy.copy(
                                        self.sets["jobs"][job_name][field][f]
                                    )
                                }
                            }
                        )

    def _prepare_directories(self):
        """Prepare directory where all batch jobs configurations will be saved.
        If it already exists it will be recreated on demand."""

        for jname, bname in self.sets["batches"].items():

            directory = os.path.join(os.environ["PYRATE"], "batch", jname)

            if os.path.isdir(directory):
                answer = input(
                    f"WARNING: path {directory} already exists.\nDo you want to delete it? "
                )
                if answer in ["y", "yes", "Y", "Yes", "YES"]:
                    shutil.rmtree(directory)
                    os.mkdir(directory)
                else:
                    # create a new directory with the date
                    # directory...
                    pass

    def _write_script(self):
        pass


# EOF
