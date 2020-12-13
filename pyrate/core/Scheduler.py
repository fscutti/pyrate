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
import time

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Scheduler:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level

    def setup(self):

        self.sets = {"logger": None, "batches": {}, "jobs": {}, "files": {}}

        # --------------------------
        # Setup the logger
        # --------------------------

        self.sets["logger"] = logging.getLogger("spyrate")
        self.sets["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        # create original job dictionary
        for jname, jattr in self.config["jobs"].items():

            self.sets["jobs"][jname] = {}

            jpath = os.path.join(os.environ["PYRATE"], "scripts")

            try:
                jpath = jattr["path"]

            except KeyError:
                pass

            for f in FN.find_files(jpath):
                if f.endswith(jname + ".yaml"):

                    self.sets["jobs"][jname].update(yaml.full_load(open(f, "r")))
                    self.sets["jobs"][jname].update(jattr)

                    break

        # create batch jobs dictionary
        for jname, jattr in self.sets["jobs"].items():

            self.sets["batches"][jname] = {}

            if "factorisation" in jattr:

                # modify event slices
                if "eparts" in jattr["factorisation"]:

                    ep = jattr["factorisation"]["eparts"]

                    jattr["factorisation"]["eparts"] = [
                        f"slice_{s+1}_nparts_{ep}" for s in range(ep)
                    ]

                for tags in list(
                    itertools.product(*list(jattr["factorisation"].values()))
                ):

                    bname = "_".join([f"{t}" for t in tags])

                    self.sets["batches"][jname][bname] = {}

            else:
                bname = jname
                self.sets["batches"][jname][bname] = {}

        for jname, bnames in self.sets["batches"].items():

            # Prepare directory where all batch jobs configurations will be saved.
            # If it already exists it will be recreated on demand.

            self.sets["files"][jname] = []

            directory = os.path.join(os.environ["PYRATE"], "batch", jname)

            if os.path.isdir(directory):
                answer = input(
                    f"WARNING: path {directory} already exists.\nDo you want to delete it? "
                )

                if answer in ["y", "yes", "Y", "Yes", "YES", "yep", "fo sho"]:
                    shutil.rmtree(directory)
                else:
                    directory += "_" + time.strftime("%Y-%m-%d-%Hh%M")

            os.mkdir(directory)

            # Transfer fields from original job dictionaries to the batch one.
            for b_idx, bname in enumerate(bnames):

                # If fields are specified in the factorisation
                # modify the settings of the original job field.
                if "factorisation" in self.sets["jobs"][jname]:

                    self._prepare_events(jname, bname)
                    self._prepare_io(jname, bname, "inputs")
                    self._prepare_io(jname, bname, "outputs")

                # Add remaining fields from the original job config file which
                # were not scheduled for modifiction.
                for field in ["inputs", "configs", "outputs"]:

                    if field in self.sets["batches"][jname][bname]:
                        continue

                    else:
                        self.sets["batches"][jname][bname].update(
                            {field: self.sets["jobs"][jname][field]}
                        )

                # dump configuration to file.
                bfile = os.path.join(directory, bname + ".yaml")

                try:
                    if self.config["jobs"][jname]["make_array"]:
                        bfile = os.path.join(directory, jname + f"_j{b_idx}" + ".yaml")

                except KeyError:
                    pass

                # Add file to the list of batch files associated to one job.
                # Then, write the configuration into the file.
                self.sets["files"][jname].append(bfile)

                with open(bfile, "w") as bf:
                    yaml.dump(self.sets["batches"][jname][bname], bf)

    def launch(self):
        pass

    def _prepare_events(self, job_name, batch_name):
        """Prepare the eslice field of the batch job."""

        if "eparts" in self.sets["jobs"][job_name]["factorisation"]:
            eparts = batch_name.split("slice", 1)[1].split("_")

            for iname, iattr in self.sets["jobs"][job_name]["inputs"].items():

                b_slice, b_nparts = eparts[1], eparts[3]

                # N.B.: this is iteratively modifying an attribute
                # of the original job. Later on this would need to be
                # copied when building the corresponding attribute of
                # the batch job.
                iattr["eslices"] = [{"slice": b_slice, "nparts": b_nparts}]

    def _prepare_io(self, job_name, batch_name, field):
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

    def _write_script(self):
        # https://dashboard.hpc.unimelb.edu.au/job_submission/
        pass


# EOF
