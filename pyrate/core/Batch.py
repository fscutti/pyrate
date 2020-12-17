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


class Batch:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level

    def setup(self):

        self.sets = {
            "logger": None,
            "jobs": {},
            "batches": {},
            "config_files": {},
            "script_files": {},
        }

        # --------------------------
        # Setup the logger
        # --------------------------

        self.sets["logger"] = logging.getLogger("spyrate")
        self.sets["logger"].setLevel(getattr(logging, self.log_level))

        # --------------------------
        # Build global configuration
        # --------------------------

        main_dir = os.path.join(os.environ["PYRATE"], "batch")

        if "batch_path" in self.config:
            main_dir = os.path.join(os.environ["PYRATE"], self.config["batch_path"])

        self.batch_dir = self._get_directory(main_dir, sub_dir=self.name)

        # create original job dictionary.
        for jname, jattr in self.config["jobs"].items():

            self.sets["jobs"][jname] = {}

            jpath = os.path.join(os.environ["PYRATE"], "scripts")

            try:
                jpath = jattr["paths"]["in"]

            except KeyError:
                pass

            for f in FN.find_files(jpath):
                if f.endswith(jname + ".yaml"):

                    self.sets["jobs"][jname].update(yaml.full_load(open(f, "r")))
                    self.sets["jobs"][jname].update(jattr)

                    break

        # create batch jobs dictionary.
        for jname, jattr in self.sets["jobs"].items():

            # create main directory here.

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

        # create configuration files dictionary.
        for jname, bnames in self.sets["batches"].items():

            self.sets["config_files"][jname] = []

            b_directory = self._get_directory(
                os.path.join(self.batch_dir, jname), sub_dir="batch_config"
            )

            # save global configuration.
            with open(os.path.join(self.batch_dir, f"{jname}_global.yaml"), "w") as g:
                yaml.dump(self.sets["jobs"][jname], g)

            # Transfer fields from original job dictionaries to the batch one.
            for b_idx, bname in enumerate(bnames):

                # If fields are specified in the factorisation
                # modify the settings of the original job field.
                if "factorisation" in self.sets["jobs"][jname]:

                    self._prepare_events(jname, bname)
                    self._prepare_io(jname, bname, "inputs")
                    self._prepare_io(jname, bname, "outputs")

                # Add remaining fields from the original job config file which
                # were not scheduled for modification.
                self._prepare_remaining_fields(jname, bname)

                make_array = False

                if "make_array" in self.config["jobs"][jname]:
                    if self.config["jobs"][jname]["make_array"]:
                        make_array = True

                b_file = self._get_config_file(
                    jname, bname, b_idx, b_directory, make_array=make_array
                )

                self.sets["config_files"][jname].append(b_file)

        # create submission scripts dictionary.
        for jname, fnames in self.sets["config_files"].items():

            self.sets["script_files"][jname] = []

            s_directory = self._get_directory(
                os.path.join(self.batch_dir, jname), sub_dir="batch_scripts"
            )

            for f_idx, fname in enumerate(fnames):

                script = {}

                make_array = False

                if "make_array" in self.config["jobs"][jname]:
                    if self.config["jobs"][jname]["make_array"]:
                        make_array = True

                s_file = self._get_script_file(
                    jname, script, f_idx, s_directory, make_array=make_array
                )

                self.sets["script_files"][jname].append(s_file)

                if make_array:
                    break

    def launch(self):
        """Submit batch jobs."""

        # ToDo: distinguish different batch submission systems.
        # ToDo: introduce job dependencies.
        # ToDo: handle input and output.
        for jname, sfiles in self.sets["script_files"].items():
            for sfile in sfiles:
                # os.system(f"sbatch {sfile}")
                print(f"sbatch {sfile}")

    def _get_directory(self, parent_dir, check=True, sub_dir=""):
        """Prepare directory containing batch configurations."""

        directory = os.path.join(parent_dir, sub_dir)

        if os.path.isdir(directory):
            if check:

                answer = input(
                    f"WARNING: path {directory} already exists.\nDo you want to delete it? "
                )

                if answer in ["y", "yes", "Y", "Yes", "YES", "yep", "fo sho"]:
                    shutil.rmtree(directory)

                else:
                    directory += "_" + time.strftime("%Y-%m-%d-%Hh%Mm%Ss")
            else:
                return directory

        os.makedirs(directory)

        return directory

    def _get_config_file(
        self, job_name, batch_name, batch_idx, batch_directory, make_array=False
    ):
        """Save configuration to .yaml file."""

        batch_file = os.path.join(batch_directory, batch_name + ".yaml")

        if make_array:
            batch_file = os.path.join(
                batch_directory, job_name + f"_j{batch_idx}" + ".yaml"
            )

        with open(batch_file, "w") as bf:
            yaml.dump(self.sets["batches"][job_name][batch_name], bf)

        return batch_file

    def _get_script_file(
        self, job_name, script, file_idx, script_directory, make_array=False
    ):
        """ Prepare script file depeding on batch submission system."""

        script_file = None

        if "slurm" in self.config["jobs"][job_name]["system"]:

            self._prepare_slurm_script(
                job_name,
                script,
                self.config["jobs"][job_name]["system"]["slurm"],
                file_idx,
                make_array=make_array,
            )

            file_name = "_".join([job_name, "array.slurm"])

            if not make_array:
                path, file_name = os.path.split(
                    self.sets["config_files"][job_name][file_idx]
                )

            script_file = os.path.join(
                script_directory, file_name.replace(".yaml", ".slurm")
            )

        with open(script_file, "w") as sf:
            for block, lines in script.items():

                for l in lines:
                    sf.write(f"{l}\n")

                sf.write("\n")

        return script_file

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

    def _prepare_remaining_fields(self, job_name, batch_name):
        """Prepare remaining fields of the batch job."""

        for field in ["inputs", "configs", "outputs"]:
            if not field in self.sets["batches"][job_name][batch_name]:

                self.sets["batches"][job_name][batch_name].update(
                    {field: self.sets["jobs"][job_name][field]}
                )

    def _prepare_slurm_script(
        self, job_name, script, slurm_config, file_idx, make_array=False
    ):
        """ Fill dictionary with slurm script lines. """

        # ToDo: support other shell types?
        script["shell"] = ["#!/bin/bash"]

        # SBATCH directives.
        script["SBATCH"] = [
            f"#SBATCH --{iname}={iattr}"
            for iname, iattr in slurm_config["SBATCH"].items()
        ]

        try:
            outpath = self.config["jobs"][job_name]["paths"]["out"]

            if outpath == "batch_path":

                outpath = os.path.join(self.batch_dir, job_name)
                outpath = self._get_directory(
                    outpath, check=False, sub_dir="batch_output"
                )

            script["SBATCH"].append(f"#SBATCH -o {outpath}/slurm.%N.%j.out # STDOUT")
            script["SBATCH"].append(f"#SBATCH -e {outpath}/slurm.%N.%j.err # STDERR")

        except KeyError:
            pass

        # sourcing scripts.
        if "source" in slurm_config:
            script["source"] = [f"source {s}" for s in slurm_config["source"]]

        # handling of modules.
        script["modules"] = []
        if "modules" in slurm_config:
            for iname, iattr in slurm_config["modules"].items():

                if iname == "purge":
                    if iattr:
                        script["modules"].append("module purge")
                if iname == "load":
                    for m in iattr:
                        script["modules"].append(f"module load {m}")

        # command to launch the main program.
        cf = self.sets["config_files"][job_name][file_idx] + " -b"
        script["command"] = [slurm_config["command"].replace("*", cf)]

        if "make_array" in self.config["jobs"][job_name]:
            if self.config["jobs"][job_name]["make_array"]:

                first_cf = self.sets["config_files"][job_name][0]
                first_cf = first_cf.replace("j0", "j{SLURM_ARRAY_TASK_ID}")

                script["command"] = [f"pyrate -j {first_cf} -b"]


# EOF
