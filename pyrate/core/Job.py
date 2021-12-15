""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

import os
import sys
import yaml
import pyclbr
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

        for i_name, i_attr in self.config["inputs"].items():

            # This dictionary contains all input information. The file list contains lists
            # which can have more than one element in the case of multiple channels declared in the group.
            self.job["inputs"][i_name] = {"files": []}

            # Files are collected looking for tags separated by underscores. Sevaral options are available
            # to collect tags.
            # 1) any: (REQUIRED) collect a file if it contains any of these tags.
            # 2) all: collect a file if it contains all of these tags.
            # 3) gropus: if a file starts with any of the tags declared here it will be considered as part of a group.
            #
            # Files can also be added providing their full path under the 'path' field. Notice that if the 'samples' options
            # are ALSO provided, all files added in this way will be selected according to the 'tags' rules as usual.

            for f in FN.find_files(i_attr["path"], "PYRATE"):

                if "samples" in i_attr:
                    self.job["inputs"][i_name]["files"].extend(
                        f
                        for s in ST.get_items(i_attr["samples"]["tags"]["any"])
                        if s in ST.get_tags(f)
                        and FN.modus_ponens(
                            "all" in i_attr["samples"]["tags"],
                            all(
                                t in ST.get_tags(f)
                                for t in ST.get_items(
                                    i_attr["samples"]["tags"].get("all", False)
                                )
                            ),
                        )
                        and FN.modus_ponens(
                            "groups" in i_attr["samples"]["tags"],
                            any(
                                c in ST.get_tags(f)
                                for c in ST.get_items(
                                    i_attr["samples"]["tags"].get("groups", False)
                                )
                            ),
                        )
                    )

                else:
                    self.job["inputs"][i_name]["files"].append(f)

            # removing duplicates from the list of files. At this stage no groups are built yet.
            self.job["inputs"][i_name]["files"] = ST.remove_duplicates(
                self.job["inputs"][i_name]["files"]
            )

            # Group files using the first tag found in their name.
            self.job["inputs"][i_name]["files"] = [
                list(f)
                for j, f in groupby(
                    self.job["inputs"][i_name]["files"],
                    lambda a: a.partition("_")[0]
                    if FN.find("groups", i_attr)
                    else None,
                )
            ]

            if not self.job["inputs"][i_name]["files"]:
                sys.exit(
                    f"ERROR: no input files found for input {i_name} under path {i_attr['path']}"
                )

            # Add all remaining attributes.
            self.job["inputs"][i_name].update(i_attr)

        self.job["configs"]["global"] = {"objects": {}}
        for c_name, c_attr in self.config["configs"].items():

            self.job["configs"][c_name] = {"files": []}

            """
            for f in FN.find_files(c_attr["path"], "PYRATE"):
                
                self.job["configs"][c_name]["files"].extend(f)

                for t in ST.get_tags(f)
                
                for s in FN.find("any", c_attr):
                   ST.get_items(s)
                   if s in ST.get_tags(f):
                       True
                for s in FN.find("all", c_attr):
                   ST.get_items(s)
                   if s in ST.get_tags(f):
                       True
            """

            for f in FN.find_files(c_attr["path"], "PYRATE"):
                self.job["configs"][c_name]["files"].extend(
                    f
                    for n in ST.get_items(c_attr["tags"]["any"])
                    if n in ST.get_tags(f)
                    and FN.modus_ponens(
                        "all" in c_attr["tags"],
                        all(
                            t in ST.get_tags(f)
                            for t in ST.get_items(c_attr["tags"].get("all", False))
                        ),
                    )
                    and f.lower().endswith(".yaml")
                )

            for f in self.job["configs"][c_name]["files"]:
                self.job["configs"][c_name].update(yaml.full_load(open(f, "r")))

            self.job["configs"]["global"]["objects"].update(
                self.job["configs"][c_name]["objects"]
            )

        for o_name, o_attr in self.config["outputs"].items():

            self.job["outputs"][o_name] = {"files": []}

            o_attr["path"] = FN.find_env(o_attr["path"], "PYRATE")

            self.job["outputs"][o_name]["files"] = os.path.join(o_attr["path"], o_name)

            for target in o_attr["targets"]:
                for t_name, t_attr in target.items():

                    if t_attr == "all":
                        samples = ST.remove_duplicates(self.job["inputs"])
                    else:
                        samples = ST.get_items(target[t_name])

                    samples.sort()

                    s_names = ",".join(samples)

                target[t_name] = samples

                target[":".join([t_name, s_names])] = target.pop(t_name)

            self.job["outputs"][o_name].update(o_attr)

        # --------------------------
        # Validate configuration
        # --------------------------

        # The configuration validation runs conservatively on all objects in the
        # configuration files passed, even if they are not needed by any target.
        for obj_name, obj_attr in self.job["configs"]["global"]["objects"].items():

            self._validate_conf(obj_name, obj_attr)

        # --------------------------
        # Build dependencies
        # --------------------------

        # Build object dependencies to guarantee that all states are run consistently.
        for obj_name, obj_attr in self.job["configs"]["global"]["objects"].items():

            self._build_dependencies(obj_name, obj_attr)

        # FN.pretty(self.job["configs"]["global"]["objects"])

        # sys.exit()

        # -----------------------
        # Instantiate Run object
        # -----------------------
        self.run = Run(f"{self.name}_run", self.job)

        self.run.setup()

    def launch(self):
        """Launch Run objects. """
        self.run.launch()

    def _validate_conf(self, obj_name, obj_conf):
        """Checks:
        1) That the configured object implements an algorithm field.
        2) That the algorithm field implements a name field.
        3) That alg_name corresponds to one pyrate module and one only.
        4) That the module contains the definition of a class called alg_name.
        5) That the states required at configuration match those implemented by the algorithm.
        6) That configured states require some input or output fields.
        """

        # Check 1
        if not FN.check("algorithm", obj_conf):
            sys.exit(
                f"ERROR: object {obj_name} has no algorithm field in its configuration!"
            )

        # Check 2
        if not FN.check("name", obj_conf["algorithm"]):
            sys.exit(f"ERROR: please specify  algorithm name for object {obj_name}!")

        pyrate_modules = [m for m in sys.modules if "pyrate" in m]

        n_alg_definitions = 0

        alg_name = obj_conf["algorithm"]["name"]

        states = ["initialise", "execute", "finalise"]

        for m in pyrate_modules:
            if alg_name == m.split(".")[-1]:

                n_alg_definitions += 1

                # Check 4
                if not alg_name in pyclbr.readmodule(f"{m}").keys():

                    sys.exit(
                        f"ERROR: module {m} has to contain an algorithm called {alg_name}!"
                    )

                alg_methods = pyclbr.readmodule(f"{m}")[alg_name].__dict__["children"]

                # some algorithms might simply want to reimplement
                # the internal methods to prepare the input, so the underscore
                # has to be replaced (see Algorithm definition).
                alg_methods = [a.replace("_", "") for a in alg_methods]

                alg_states = set([s for s in alg_methods if s in states])

                conf_states = set([s for s in states if FN.check(s, obj_conf)])

                # Check 5
                if not alg_states == conf_states:
                    sys.exit(
                        f"ERROR: states mismatch b/w object {obj_name} and algorithm {alg_name}!"
                    )

                # Check 6
                for s in conf_states:
                    if not (
                        FN.check("input", obj_conf[s])
                        or FN.check("output", obj_conf[s])
                    ):
                        sys.exit(
                            f"ERROR: state {s} for object {obj_name} has no input or output fields defined!\nPlease add at least one of the fields"
                        )

        # Check 3
        if n_alg_definitions == 0:
            e_msg = f"ERROR: while checking the configuration for {obj_name}, no suitable {alg_name} module has been found!\n"
            e_msg += "1) The algorithm / module has to be added to its local __init__.py file.\n"
            e_msg += "2) Make sure the name of the algorithm is written correctly.\n"
            e_msg += "3) The module and the algorithm have to have the same name.\n"
            sys.exit(e_msg)

        elif n_alg_definitions > 1:
            sys.exit(
                f"ERROR: while checking the configuration for {obj_name}, {n_alg_definitions} definitions of a module called {alg_name} have been found!"
            )

    def _build_dependencies(self, obj_name, obj_conf):
        """Adds consistent dependencies from the global configuration."""

        g_config = self.job["configs"]["global"]["objects"]

        states = ["initialise", "execute", "finalise"]

        if not "dependency" in obj_conf:
            obj_conf["dependency"] = {
                "initialise": set(),
                "execute": set(),
                "finalise": set(),
            }

        for s_idx, s in enumerate(states):

            prev_states = states[:s_idx]

            if s in obj_conf:

                if "input" in obj_conf[s]:

                    for o in ST.get_items(obj_conf[s]["input"]):

                        if not o in g_config:

                            if self._is_required(o, prev_states, obj_conf):

                                sys.exit(
                                    f"ERROR: {o} is required by {obj_name} for {s} but is not in the global configuration!"
                                )

                        else:
                            obj_conf["dependency"][s].add(o)

                            for ps in prev_states:
                                if ps in g_config[o]:

                                    obj_conf["dependency"][ps].add(o)

                # If the object relies on an initialise or finalise method, these have to put
                # on the permanent store some data identifiable with the object name.
                """
                if s == ["initialise", "finalise"]:

                    if not "output" in obj_conf[s]:
                        obj_conf[s]["output"] = "SELF"

                    else:
                        if not "SELF" in ST.get_items(obj_conf[s]["output"]):
                            obj_conf[s]["output"] += f", SELF"
                """

        # This is to guarantee a consistent construction of dependency across all states.
        obj_conf["dependency"]["execute"].union(obj_conf["dependency"]["finalise"])
        obj_conf["dependency"]["initialise"].union(obj_conf["dependency"]["execute"])

    def _is_required(self, dep_obj_name, prev_states, obj_conf):
        """Returns False if an object is not computed upstream by an algorithm."""

        if "EVENT:" in dep_obj_name:
            return False

        if "INPUT:" in dep_obj_name:
            return False

        for ps in prev_states:

            if ps in obj_conf:

                if "output" in obj_conf[ps]:

                    if dep_obj_name in ST.get_items(obj_conf[ps]["output"]):
                        return True

        return False


# EOF
