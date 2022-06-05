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

        # will handle this within the algorithm.
        # self.alg_times = defaultdict(
        #    float
        # )  # Initialising the alg_times dictionary which stores the average run times of each alg

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

        # Will need to change handling of log files.

        """
        while os.path.exists(log_file_name):
            base_name = log_file_name.split(".log")[0]

            if base_name[-2] == "_":
                log_file_name = base_name[:-1] + str(int(base_name[-1]) + 1) + ".log"

            else:
                log_file_name = base_name + "_1.log"
        """

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

        self.store = Store(self.name)

        self.targets = {}
        self.nodes = {}
        self.algorithms = {}

        for out_name, out_config in self.outputs.items():
            for t_dict in out_config["targets"]:
                for t_name, t_samples in t_dict.items():

                    obj_name = t_name.split(":")[0]

                    self.targets[t_name] = self.node(t_name, samples=t_samples)

                    # print(RenderTree(self.targets[t_name]))

    def node(self, obj_name, samples=None):
        """Gets node tree of an object.
        This is a recursive function."""

        if obj_name in self.nodes:
            return self.nodes[obj_name]

        else:
            self.nodes[obj_name] = Node(
                obj_name, algorithm=self.alg(obj_name), samples=samples
            )

            if self.nodes[obj_name].algorithm is not None:

                for i in self.nodes[obj_name].algorithm.input:

                    try:
                        self.node(i).parent = self.nodes[obj_name]

                    except anytreeExceptions.LoopError:
                        sys.exit(
                            f"ERROR: circular node detected between {i} and {obj_name}"
                        )

        return self.nodes[obj_name]

    def alg(self, obj_name):
        """Gets instance of algorithm from the configuration."""

        if obj_name in self.algorithms:
            return self.algorithms[obj_name]

        else:
            # obj_name might be a target
            # containining the sample names. There are other
            # manipulations of the obj_name too for example
            # "multiplying" channels.

            obj = obj_name.split(":")[0]

            if obj in self._config:

                obj_config = self._config[obj]

                for m in sys.modules:
                    if obj_config["algorithm"] == m.split(".")[-1]:

                        self.algorithms[obj_name] = getattr(
                            importlib.import_module(m), m.split(".")[-1]
                        )(obj_name, obj_config, self.store, self.logger)

                        self.algorithms[obj_name].input = obj_config["input"]

                        if "output" in obj_config:
                            self.algorithms[obj_name].output = obj_config["output"]
                        else:
                            self.algorithms[obj_name].output = ""

                        return self.algorithms[obj_name]

            elif obj == "EVENT" or obj == "INPUT":
                pass

            else:
                sys.exit(f"ERROR: object {obj} not defined in the configuration.")

    def launch(self):
        """Implement input/output loop."""
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        start = timeit.default_timer()

        # self.store.put("history", self._history, "PERM")

        # -----------------------------------------------------------------------
        # Instanciate/load the output. Files are opened and ready to be written.
        # -----------------------------------------------------------------------

        self._out = Output(self.name, self.store, self.logger, outputs=self.outputs)

        if not self._out.is_loaded:
            self._out.load()

        # maybe change the way this is retrieved. Use nodes directly.
        all_inputs_vs_targets = self._out.get_inputs_vs_targets()

        # -----------------------------------------------------------------------
        # Instanciate algorithms for all targets specified in the job options.
        # -----------------------------------------------------------------------
        # print(all_inputs_vs_targets)

        # self.algorithms = {}
        # for i_name, targets in all_inputs_vs_targets.items():
        #    for t in targets:

        #        alg_name = self._config[t["object"]]["algorithm"]["name"]
        #        obj_name = t["name"]

        #        self.add(obj_name, alg_name, store)

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
            # current_inputs_vs_targets = self.update_inputs_vs_targets(
            #    state, store, all_inputs_vs_targets
            # )

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
                # if self.alg_timing:
                #    for alg in sorted(self.algorithms):
                #        if self.alg_timing == True:
                #            self.logger.info(
                #                f"{self.algorithms[alg].name:<40}{self.alg_times[alg]/erange:>20.2f} ns"
                #            )
                #        elif self.alg_timing == "print" or self.alg_timing == "p":
                #            print(
                #                f"{self.algorithms[alg].name:<40}{self.alg_times[alg]/erange:>20.2f} ns"
                #            )

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

    def loop(self):
        """Loop over required targets to resolve them. Skips completed ones."""
        for t in self.targets:
            self.call(t)

    def call(self, obj_name):
        """Calls an algorithm."""

        if self.store.get(obj_name) is enums.Pyrate.NONE:

            alg = self.nodes[obj_name].algorithm

            if alg is not None:

                # preparing input
                if not self.is_done(obj_name, alg):

                    getattr(alg, self.state)()

                # checking ouput.
                if not self.is_complete(obj_name, alg):
                    sys.exit(
                        f"ERROR: object {obj_name} is on the store but additional output is missing !!!"
                    )

            else:
                self._in.read(obj_name)

        return

    def is_done(self, obj_name, alg):
        """In order to get out of the dependency loop
        the algorithm has to put False on the store."""

        for dep_name, dep_cond in alg.input.items():

            self.call(dep_name)

            if dep_cond is not None:

                getattr(alg, self.state)(dep_cond)

                if not self.store.get(obj_name):
                    return True

        return False

    def is_complete(self, obj_name, alg):
        """If the main object is on the store with a valid value,
        additional output is checked to be on the store."""

        if self.store.get(obj_name) is not enums.Pyrate.NONE:

            return all(
                [
                    self.store.get(o) is not enums.Pyrate.NONE
                    for o in alg.output[obj_name]
                ]
            )

        else:
            return True

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
