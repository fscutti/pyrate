""" This class controls the execution of algorithms
    as a single local instance. 
"""
import os
import sys
import importlib
import timeit
import time
import logging
import anytree.node.exceptions as anytreeExceptions

from cmath import log
from collections import defaultdict
from anytree import Node, RenderTree

from colorama import Fore
from tqdm import tqdm

from pyrate.core.Store import Store
from pyrate.core.Input import Input
from pyrate.core.Output import Output

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums as EN


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
        self._current_input = None
        self._config = self.configs["global"]["objects"]

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

        blue = "{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET)
        yellow = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.YELLOW,
            Fore.RESET,
        )
        green = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.GREEN,
            Fore.RESET,
        )
        white = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.WHITE,
            Fore.RESET,
        )

        self.colors = {"blue": blue, "yellow": yellow, "green": green, "white": white}

        self.store = Store(self.name)

        self.targets = {}
        self.nodes = {}
        self.algorithms = {}
        self.loaded_io = {"inputs": {}, "outputs": {}}

        # loading outputs.
        for o_name in self.outputs:
            o = self.io(o_name)

        # initialising algorithms/objects.
        for out_name in self.outputs:
            for t_name, t_samples in self.io(out_name).targets.items():
                self.targets[t_name] = self.node(t_name, samples=t_samples)

        # loading inputs.
        for t_name, t_instance in self.targets.items():
            for i_name in t_instance.samples:
                i = self.io(i_name)

    def io(self, io_name):
        """Returns a specific output instance."""

        for category in ["inputs", "outputs"]:
            if io_name in self.loaded_io[category]:

                return self.loaded_io[category][io_name]

        else:

            if io_name in self.inputs:

                io_config = self.inputs[io_name]

                self.loaded_io["inputs"][io_name] = Input(
                    io_name, io_config, self.store, self.logger
                )

                self.loaded_io["inputs"][io_name].load()

                return self.loaded_io["inputs"][io_name]

            elif io_name in self.outputs:

                io_config = self.outputs[io_name]

                self.loaded_io["outputs"][io_name] = Output(
                    io_name, io_config, self.store, self.logger
                )

                self.loaded_io["outputs"][io_name].load()

                return self.loaded_io["outputs"][io_name]

            else:
                sys.exit(
                    f"ERROR: input / ouput {io_name} not defined in the configuration."
                )
                return None

    def node(self, obj_name, samples=[]):
        """Gets node tree of an object. This is a recursive function."""
        if not obj_name in self.nodes:

            self.nodes[obj_name] = Node(obj_name, algorithm=None, samples=samples)

        if self.nodes[obj_name].algorithm is None:

            self.nodes[obj_name].algorithm = self.alg(obj_name)

            if (
                self.nodes[obj_name].algorithm is not None
                and not self.nodes[obj_name].children
            ):

                for i in self.nodes[obj_name].algorithm.input:

                    try:
                        self.node(i).parent = self.nodes[obj_name]

                    except anytreeExceptions.LoopError:
                        sys.exit(
                            f"ERROR: circular node detected between {i} and {obj_name}"
                        )

        return self.nodes[obj_name]

    def reset(self):
        """Clears the algorithm instance of a node."""
        for obj_name in list(self.algorithms.keys()):

            del self.algorithms[obj_name]

            self.nodes[obj_name].algorithm = None

    def alg(self, obj_name):
        """Gets instance of algorithm from the configuration."""

        if obj_name in self.algorithms:
            return self.algorithms[obj_name]

        else:
            obj = obj_name.split(":")[0]

            if obj in self._config:

                obj_config = self._config[obj]

                for m in sys.modules:

                    alg_name = m.split(".")[-1]

                    if obj_config["algorithm"] == alg_name:

                        module = importlib.import_module(m)

                        # algorithm instance.
                        self.algorithms[obj_name] = getattr(module, alg_name)(
                            obj_name, obj_config, self.store, self.logger
                        )

                        # initialisation of inputs and outputs.
                        self.algorithms[obj_name].input = obj_config["input"]

                        if "output" in obj_config:
                            self.algorithms[obj_name].output = obj_config["output"]
                        else:
                            self.algorithms[obj_name].output = ""

                        return self.algorithms[obj_name]

            elif obj in ["EVENT", "INPUT"]:
                return None

            else:
                sys.exit(f"ERROR: object {obj} not defined in the configuration.")

    def launch(self):
        """Implement input/output loop."""
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        start = timeit.default_timer()

        msg = f"Launching pyrate run {self.name}"
        print("\n", "*" * len(msg), msg, "*" * len(msg))

        for i_name in tqdm(
            self.loaded_io["inputs"],
            desc="Input loop".ljust(70, "."),
            disable=self.no_progress_bar,
            bar_format=self.colors["blue"],
        ):

            self._current_input = self.loaded_io["inputs"][i_name]

            for state in ["initialise", "execute", "finalise"]:

                self.state = state

                self.run(i_name)

            self.reset()

        for o_name in tqdm(
            self.loaded_io["outputs"],
            desc="Output loop".ljust(70, "."),
            disable=self.no_progress_bar,
            bar_format=self.colors["green"],
        ):

            for t_name in self.targets:

                self._current_output = self.loaded_io["outputs"][o_name]

                self._current_output.write(t_name)

        stop = timeit.default_timer()

        if self.no_progress_bar:
            print("Execution time: ", str(stop - start))

        # self.logger.info("Execution time: ", str(stop - start))

        return

    def run(self, i_name):
        """Run the loop function."""

        if self.state in ["initialise", "finalise"]:
            # ---------------------------------------------------------------
            # Initialise and finalise loops
            # ---------------------------------------------------------------
            self.store.put("INPUT:name", i_name)

            self.store.put("INPUT:config", self.inputs[i_name])

            self.loop()

        elif self.state == "execute":
            # ---------------------------------------------------------------
            # Execute loop
            # ---------------------------------------------------------------

            # print("Prepare total number of events for event loop.")

            tot_n_events = self._current_input.get_n_events()

            # print(f"Total number of events for input {self._current_input.name}: {tot_n_events}")

            eslices = self.get_events_slices(tot_n_events)

            # print(f"Total eslices for input {self._current_input.name}: {eslices}")
            # ---------------------------------------------------------------
            # Event loop
            # ---------------------------------------------------------------

            info = "Event loop"

            for emin, emax in eslices:

                info += f"({i_name},  emin: {emin},  emax: {emax})".rjust(60, ".")

                # print(f"Emin, Emax: {emin}, {emax}")

                self._current_input.set_idx(emin)

                erange = emax - emin + 1

                for idx in tqdm(
                    range(erange),
                    desc=f"{info}",
                    disable=self.no_progress_bar,
                    bar_format=self.colors["white"],
                ):
                    self.store.put("INPUT:name", i_name)

                    self.store.put("INPUT:config", self.inputs[i_name])

                    self.store.put("EVENT:idx", self._current_input.get_idx())

                    self.loop()

                    # print("About to call set next event")
                    self._current_input.set_next_event()

    def loop(self):
        """Loop over required targets to resolve them."""
        for t_name, t_instance in self.targets.items():

            if self._current_input.name in t_instance.samples:

                # print(f"Currently calling {t_name} for {self._current_input.name}")

                self.call(t_name)

        self.store.clear()

    def call(self, obj_name):
        """Calls an algorithm."""

        if self.store.get(obj_name) is EN.Pyrate.NONE:

            alg = self.node(obj_name).algorithm

            if alg is not None:

                # check whether the obj meets the alg conditions to run.
                if self.is_meeting_alg_conditions(obj_name, alg):

                    # print(f"Calling algorithm {alg.name} in state: {self.state} after meeting conditions.")
                    getattr(alg, self.state)()

                # checking that the object is complete.
                # if not self.is_complete(obj_name, alg):
                #    sys.exit(
                #        f"ERROR: object {obj_name} is on the store but additional output is missing !!!"
                #    )

            else:
                self._current_input.read(obj_name)

        return

    def is_meeting_alg_conditions(self, obj_name, alg):
        """In order to get out of the dependency loop
        the algorithm has to put False/0 on the store."""

        n_deps = len(alg.input) - 1

        for dep_idx, dep_name in enumerate(alg.input):

            self.call(dep_name)

            dep_cond = alg.input[dep_name]

            if dep_cond is not None:

                passed = getattr(alg, self.state)(dep_cond)

                if not passed or dep_idx == n_deps:
                    return False

        return True

    def is_complete(self, obj_name, alg):
        """If the main object is on the store with a valid value,
        additional output is checked to be on the store."""

        if self.store.get(obj_name) is not EN.Pyrate.NONE:

            return all(
                [self.store.get(o) is not EN.Pyrate.NONE for o in alg.output[obj_name]]
            )

        else:
            return True

    def get_events_slices(self, tot):
        """Updates emin and emax attributes for running on valid slice."""

        eslices = []

        # ---------------------------------------------------------------
        # Reading input events
        # ---------------------------------------------------------------
        if hasattr(self._current_input, "eslices"):

            if isinstance(self._current_input.eslices, dict):
                emin, emax = 0, tot - 1

                if "emin" in self._current_input.eslices:
                    emin = self._current_input.eslices["emin"]

                if (
                    "emax" in self._current_input.eslices
                    and self._current_input.eslices["emax"] > -1
                ):
                    emax = self._current_input.eslices["emax"]

                eslices.append((emin, emax))

            elif isinstance(self._current_input.eslices, list):

                for s in self._current_input.eslices:

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
                emin, emax = 0, self._current_input.eslices - 1

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
