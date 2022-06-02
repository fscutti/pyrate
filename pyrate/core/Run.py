""" This class controls the execution of algorithms
    as a single local instance. 
"""
from cmath import log
import os
import sys
import importlib
import timeit
import time
import logging
from collections import defaultdict
from anytree import Node, RenderTree

import anytree.node.exceptions as anytreeExceptions

from colorama import Fore
from tqdm import tqdm

from pyrate.core.Store import Store
from pyrate.core.Input import Input
from pyrate.core.Output import Output

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums


class Run:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name
        self.alg_times = defaultdict(
            float
        )  # Initialising the alg_times dictionary which stores the average run times of each alg

    def setup(self):
        """First instance of 'private' members."""
        # -----------------------------------------------------------------------
        # At this point the Run object should have self.input/config/output
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------
        self.state = None
        self._in = None
        self._out = None
        self._config = self.configs["global"]["objects"]

        self._history = {"CURRENT TARGET": None}

        log_file_name = f"{self.name}.{time.strftime('%Y-%m-%d-%Hh%M')}.log"
        # Handles the case where log files have the same name
        while os.path.exists(log_file_name):
            base_name = log_file_name.split(".log")[0]

            if base_name[-2] == "_":
                log_file_name = base_name[:-1] + str(int(base_name[-1]) + 1) + ".log"

            else:
                log_file_name = base_name + "_1.log"

        fileHandler = logging.FileHandler(log_file_name, delay=True)

        fileHandler.setFormatter(
            logging.Formatter("[%(asctime)s %(name)-16s %(levelname)-7s]  %(message)s")
        )

        self.logger.addHandler(fileHandler)

        self.colors = {"initialise": {}, "execute": {}, "finalise": {}}

        self.colors["initialise"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.BLUE,
            Fore.RESET,
        )
        self.colors["execute"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.YELLOW,
            Fore.RESET,
        )
        self.colors["finalise"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.GREEN,
            Fore.RESET,
        )
        self.colors["execute"]["event"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.WHITE,
            Fore.RESET,
        )

        # for now this is just a temporary initialisation.
        self.store = Store(None)

        self.targets = {}
        self.trees = {}

        # This is a list where each item is a dependency tree.
        self.algorithms = {}

        for out_name, out_config in self.outputs.items():
            for t_dict in out_config["targets"]:
                for t_name, t_samples in t_dict.items():

                    obj_name = t_name.split(":")[0]

                    self.targets[t_name] = self.dependency(t_name, samples=t_samples)

                    # print(RenderTree(self.targets[t_name], style=AsciiStyle()))
                    print(RenderTree(self.targets[t_name]))

        sys.exit()

    def target(self, obj_name, samples):
        """
        try:
            return self.targets[obj_name]

        except KeyError:
            pass

        self.targets
        """
        pass

    def dependency(self, obj_name, samples=None):
        """Gets dependency tree of an object.
        This is a recursive function.
        Todo(?) Transform this into a getter method."""

        try:
            return self.trees[obj_name]

        except KeyError:
            pass

        self.trees[obj_name] = Node(
            obj_name, algorithm=self.alg(obj_name), samples=samples
        )

        if self.trees[obj_name].algorithm is not None:

            for i in self.trees[obj_name].algorithm.input:

                try:
                    self.dependency(i).parent = self.trees[obj_name]

                except anyExceptions.LoopError:
                    sys.exit(
                        f"ERROR: circular dependency detected between {i} and {obj_name}"
                    )

        return self.trees[obj_name]

    def alg(self, obj_name):
        """Gets instance of algorithm from the configuration.
        Todo(?) Transform this into a getter method."""

        try:
            return self.algorithms[obj_name]

        except KeyError:
            pass

        try:
            # obj_name might be a target
            # containining the sample names. There are other
            # manipulations of the obj_name too for example
            # "multiplying" channels.
            obj_config = self._config[obj_name.split(":")[0]]

            for m in sys.modules:
                if obj_config["algorithm"] == m.split(".")[-1]:

                    self.algorithms[obj_name] = getattr(
                        importlib.import_module(m), m.split(".")[-1]
                    )(obj_name, obj_config, self.store, self.logger)

                    self.algorithms[obj_name].input = obj_config["input"]

                    return self.algorithms[obj_name]

        except KeyError:
            """Error message here. Let EVENT or INPUT pass."""
            pass

    def launch(self):
        """Implement input/output loop."""
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        start = timeit.default_timer()

        store = Store(self)

        store.put("history", self._history, "PERM")

        # -----------------------------------------------------------------------
        # Instanciate/load the output. Files are opened and ready to be written.
        # -----------------------------------------------------------------------

        self._out = Output(self.name, store, self.logger, outputs=self.outputs)

        if not self._out.is_loaded:
            self._out.load()

        all_inputs_vs_targets = self._out.get_inputs_vs_targets()

        # -----------------------------------------------------------------------
        # Instanciate algorithms for all targets specified in the job options.
        # -----------------------------------------------------------------------

        self.algorithms = {}
        for i_name, targets in all_inputs_vs_targets.items():
            for t in targets:

                alg_name = self._config[t["object"]]["algorithm"]["name"]
                obj_name = t["name"]

                self.add(obj_name, alg_name, store)

        # -----------------------------------------------------------------------
        # Inputs will be initialised dynamically in the run function.
        # -----------------------------------------------------------------------
        self.instanciated_inputs = {}

        # -----------------------------------------------------------------------
        # Update the store in three steps: initialise, execute, finalise.
        # -----------------------------------------------------------------------

        msg = f"Launching pyrate run {self.name}"
        print("\n", "*" * len(msg), msg, "*" * len(msg))

        for state in ["initialise", "execute", "finalise"]:

            # updating list of targets to be considered for the next loop.
            current_inputs_vs_targets = self.update_inputs_vs_targets(
                state, store, all_inputs_vs_targets
            )

            # update the store.
            store = self.run(state, store, current_inputs_vs_targets)

        print("\n")

        stop = timeit.default_timer()

        if self.no_progress_bar:
            print("Execution time: ", str(stop - start))

        # self.logger.info("Execution time: ", str(stop - start))

        return store

    def run(self, state, store, inputs_vs_targets):
        """Run the loop function."""

        prefix_types = {
            "initialise": "Inputs:  ",
            "execute": "Events:  ",
            "finalise": "Inputs: ",
        }

        self.state = state

        prefix = prefix_types[state]

        info = self.state.rjust(70, ".")

        for i_name, targets in tqdm(
            inputs_vs_targets.items(),
            desc=f"{prefix}{info}",
            disable=self.no_progress_bar,
            bar_format=self.colors[self.state]["input"],
        ):

            # if there are no targets for this state, skip all loops.
            if not targets:
                continue

            if not i_name in self.instanciated_inputs:
                self.instanciated_inputs[i_name] = Input(
                    i_name, store, self.logger, self.inputs[i_name]
                )

            self._in = self.instanciated_inputs[i_name]

            if not self._in.is_loaded:
                self._in.load()

            if self.state in {"initialise", "finalise"}:
                # ---------------------------------------------------------------
                # Initialise and finalise loops
                # ---------------------------------------------------------------
                store.put("INPUT:name", i_name, "TRAN")
                store.put("INPUT:config", self.inputs[i_name], "TRAN")

                self.loop(store, targets)

                store.clear("TRAN")

            elif self.state == "execute":
                # ---------------------------------------------------------------
                # Execute loop
                # ---------------------------------------------------------------

                tot_n_events = self._in.get_n_events()

                eslices = self.get_events_slices(tot_n_events)

                # ---------------------------------------------------------------
                # Event loop
                # ---------------------------------------------------------------

                for emin, emax in eslices:

                    info = (
                        f"{self.state} ({i_name},  emin: {emin},  emax: {emax})".rjust(
                            70, "."
                        )
                    )

                    self._in.set_idx(emin)

                    erange = emax - emin + 1

                    for idx in tqdm(
                        range(erange),
                        desc=f"{prefix}{info}",
                        disable=self.no_progress_bar,
                        bar_format=self.colors[self.state]["event"],
                    ):
                        store.put("INPUT:name", i_name, "TRAN")
                        store.put("INPUT:config", self.inputs[i_name], "TRAN")
                        store.put("EVENT:idx", self._in.get_idx())

                        self.loop(store, targets)

                        store.clear("TRAN")

                        self._in.set_next_event()

                # Printing average time taken to execute an alg for a single event
                if self.alg_timing:
                    for alg in sorted(self.algorithms):
                        if self.alg_timing == True:
                            self.logger.info(
                                f"{self.algorithms[alg].name:<40}{self.alg_times[alg]/erange:>20.2f} ns"
                            )
                        elif self.alg_timing == "print" or self.alg_timing == "p":
                            print(
                                f"{self.algorithms[alg].name:<40}{self.alg_times[alg]/erange:>20.2f} ns"
                            )

                self._in.offload()

        if self.state == "finalise":
            # ---------------------------------------------------------------
            # Write outputs after finalise input loop
            # ---------------------------------------------------------------

            for t in targets:

                if not store.check(t["name"], "PERM"):
                    msg = f"finalise has been run for {t['name']} but object has not been put on PERM store!!!"

                    sys.exit(f"ERROR: {msg}")
                    self.logger.error(msg)

                else:
                    if store.get(t["name"], "PERM") is not enums.Pyrate.SKIP_WRITE:
                        self._out.write(t["name"])

        return store

    def loop(self, store, targets):
        """Loop over required targets to resolve them. Skips completed ones."""
        for t in targets:

            self._history[t["name"]] = []

            self._target_history = self._history[t["name"]]

            self._history["CURRENT TARGET"] = t["name"]

            self.call(t["object"], target_name=t["name"])

    def call(self, obj_name, target_name=""):
        """Calls an algorithm."""

        # print(f"calling {obj_name} is target: ({is_target})")

        alg = None

        # Assign the name attribute in the config dictionary here.
        # This might be done best in the Job class though...
        if target_name:
            alg = self.algorithms[target_name]

        else:
            alg = self.algorithms[obj_name]

        entry = f"{obj_name}:{alg.name}:TARGET({target_name})"

        if entry in self._target_history:

            self.get_history(show=True)

            FN.pretty(self._config[obj_name])

            sys.exit(f"ERROR:{entry} already executed")

        else:

            self._target_history.append(entry)

            # preparing input variables
            getattr(alg, f"_{self.state}")()
            # Timing the algorithm if timing is flagged
            if self.alg_timing:
                t1 = time.time_ns()
                # executing main algorithm state
                getattr(alg, self.state)()
                t2 = time.time_ns()
                self.alg_times[alg.name] += t2 - t1
            else:
                # executing main algorithm state
                getattr(alg, self.state)()

    def update_inputs_vs_targets(self, state, store, inputs_vs_targets):
        """Updates the dictionary containing all the targets relative to an input."""

        new_inputs_vs_targets = dict.fromkeys(inputs_vs_targets.keys(), [])

        for i_name, targets in inputs_vs_targets.items():
            for t in targets:

                if not ":" + i_name in t["name"] or "," + i_name in t["name"]:
                    continue

                # we cannot immediately "get" the target value, as this might trigger
                # the update_store function and we don't want to do that at this stage.
                if store.check(t["name"], "PERM"):

                    if store.get(t["name"], "PERM") is enums.Pyrate.SKIP_NEXT_STATE:
                        continue

                if not FN.check_dict_in_list(new_inputs_vs_targets[i_name], t):
                    new_inputs_vs_targets[i_name].append(t)

        return new_inputs_vs_targets

    def update_store(self, obj_name, store):
        """Updates value of object on the store.
        N.B. obj_name here is never the name of a target.
        This method is never called for targets as they are called explicitly in the loop."""

        if not obj_name in self._config:
            self._in.read(obj_name)
            return

        else:
            alg_name = self._config[obj_name]["algorithm"]["name"]

            try:
                alg_instance = self.algorithms[obj_name]

            except KeyError:
                self.add(obj_name, alg_name, store)

            self.call(obj_name)
            return

    def get_history(self, show=False):
        """Returns the algorithm history."""
        if show:
            FN.pretty(self._history)
        return self._history

    def get_events_slices(self, tot):
        """Updates emin and emax attributes for running on valid slice."""

        eslices = []

        # ---------------------------------------------------------------
        # Reading input events
        # ---------------------------------------------------------------
        if hasattr(self._in, "eslices"):

            if isinstance(self._in.eslices, dict):
                emin, emax = 0, tot - 1

                if "emin" in self._in.eslices:
                    emin = self._in.eslices["emin"]

                if "emax" in self._in.eslices and self._in.eslices["emax"] > -1:
                    emax = self._in.eslices["emax"]

                eslices.append((emin, emax))

            elif isinstance(self._in.eslices, list):

                for s in self._in.eslices:

                    if "slice" in s:

                        s_nparts = int(s["nparts"])
                        s_slice = "all"

                        if not s["slice"] == "all":
                            s_slice = int(s["slice"])

                        part = int(tot / s_nparts)

                        emin, emax = 0, part - 1

                        for s_idx in range(s_nparts):

                            if not s_slice == "all":
                                if s_idx == s_slice - 1:

                                    if s_idx == s_nparts - 1:
                                        eslices.append((emin, tot - 1))
                                        break

                                    else:
                                        eslices.append((emin, emax))
                                        break

                            else:
                                if s_idx == s_nparts - 1:
                                    eslices.append((emin, tot - 1))
                                else:
                                    eslices.append((emin, emax))

                            emin += part
                            emax += part

                    else:
                        emin, emax = 0, tot - 1

                        if "emin" in s:
                            emin = s["emin"]

                        if "emax" in s and s["emax"] > -1:
                            emax = s["emax"]

                        eslices.append((emin, emax))

            else:
                emin, emax = 0, self._in.eslices - 1

                eslices.append((emin, emax))

        for emin, emax in eslices:
            self.check_events_slices(emin, emax, tot)

        return eslices

    def check_events_slices(self, emin, emax, tot):
        """Validate events slice."""

        if not emin <= emax <= tot - 1:
            sys.exit(
                f"ERROR: required input range not valid. emin:{emin} <= emax:{emax} <= {tot - 1}"
            )


# EOF
