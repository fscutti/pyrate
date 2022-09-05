""" This class controls the execution of algorithms
    as a single local instance. 
"""
import os
import sys
import yaml
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
        
        print(self.configs)
        print(self.inputs)
        print(self.outputs)

        
        self.objects = {}
        for c_file in self.configs:
            f = FN.find_env(c_file, "PYRATE")
            self.objects.update(yaml.full_load(open(f, "r"))["objects"])
        

        # -----------------------------------------------------------------------
        # At this point the Run object should have self.inputs/objects/outputs
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------

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
        
        # the following two lines are temporary.
        self.logger = logging.getLogger("pyrate")
        self.logger.addHandler(fileHandler)

        blue = "{l_bar}%s{bar}%s{r_bar}"
        yellow = "{l_bar}%s{bar}%s{r_bar}"
        green = "{l_bar}%s{bar}%s{r_bar}"
        white = "{l_bar}%s{bar}%s{r_bar}"

        blue = blue % (Fore.BLUE, Fore.RESET)
        yellow = yellow % (Fore.YELLOW, Fore.RESET)
        green = green % (Fore.GREEN, Fore.RESET)
        white = white % (Fore.WHITE, Fore.RESET)

        self.colors = {"blue": blue, "yellow": yellow, "green": green, "white": white}

        self.state = None

        self._current_input = None
        self._current_output = None

        self.store = Store(self.name)

        self.targets, self.nodes, self.algorithms, self.readers = {}, {}, {}, {}
        self.loaded_io = {"inputs": {}, "outputs": {}}

        # instantiate all algorithms even those not needed.
        self._reset_algorithms_instance()

        sys.exit()
        # Loading input / output and initialising nodes.
        # Not all inputs are loaded. Only those relevant for
        # requested targets.




        # from this line on there will be major restructurings
        # one can eliminate targets.



        t_io = {}

        for o_name in self.outputs:
            o = self.io(o_name)

            for t_name, t_job_inputs in o.targets.items():

                if not t_name in self.targets:

                    # Where the magic happens!
                    # Dependecies for this target are all
                    # resolved recursively here

                    self.targets[t_name] = self.node(t_name)

                    t_io[t_name] = {"job_inputs": t_job_inputs, "job_outputs": [o_name]}

                else:
                    t_io[t_name]["job_outputs"].append(o_name)

                for i_name in t_job_inputs:
                    i = self.io(i_name)

        # initialising job inputs / outputs for the targets.
        for t_name in self.targets:

            if self.node(t_name).job_inputs == []:
                self.node(t_name).job_inputs = t_io[t_name]["job_inputs"]

            if self.node(t_name).job_outputs == []:
                self.node(t_name).job_outputs = t_io[t_name]["job_outputs"]


    """
    this will die.
    def io(self, io_name):

        for category in ["inputs", "outputs"]:
            if io_name in self.loaded_io[category]:

                return self.loaded_io[category][io_name]

        if io_name in self.inputs:

            io_config, category = self.inputs[io_name], "inputs"

            self.loaded_io[category][io_name] = Input(
                io_name, io_config, self.store, self.logger
            )

        elif io_name in self.outputs:

            io_config, category = self.outputs[io_name], "outputs"

            self.loaded_io[category][io_name] = Output(
                io_name, io_config, self.store, self.logger
            )

        else:
            sys.exit(
                f"ERROR: input / ouput {io_name} not defined in the configuration."
            )

        self.loaded_io[category][io_name].load()

        return self.loaded_io[category][io_name]
    """

    def node(self, obj_name, job_inputs=[], job_outputs=[]):
        """Instantiates a node for an object, including the corresponding algorithm instance
        and the list of relevant samples. This function checks for circular dependencies.
        The node instance is returned. This is a recursive function."""

        # this call is necessary to find the correct algorithm for secondary outputs.
        # N.B.: all object calls first pass through the node function.

        # Node already exists, just return it
        if obj_name in self.nodes:
            return self.nodes[obj_name]

        # Create a new node
        new_node = Node(
            obj_name,
            was_called=False,
            algorithm=None,
            job_inputs=job_inputs,
            job_outputs=job_outputs,
        )

        # Create a new algorithm
        new_node.algorithm = self.alg(obj_name)

        # Check if it's an input type or alg type
        if new_node.algorithm is not None:

            for _, node in self.nodes.items():

                if new_node.algorithm == node.algorithm:

                    self.nodes[obj_name] = node
                    return self.nodes[obj_name]

            # Check for children
            if not new_node.children:

                for _, dependencies in new_node.algorithm.input.items():

                    for d in dependencies:

                        try:
                            # Set this current node as the parent to the dependency
                            # being created in self.node(d)
                            self.node(d).parent = new_node

                        except anytreeExceptions.LoopError:
                            sys.exit(
                                f"ERROR: circular node detected between {d} and {obj_name}"
                            )

        self.nodes[obj_name] = new_node

        # Return our finished node
        return self.nodes[obj_name]

    def _reset_nodes_status(self):
        """Resets all node's was_called flag"""
        for obj_name in self.nodes:

            self.nodes[obj_name].was_called = False

    def _reset_algorithms_instance(self):
        """Clears all algorithm instances."""
        for obj_name in self.nodes:

            if self.nodes[obj_name].algorithm is not None:

                del self.algorithms[obj_name]

                self.nodes[obj_name].algorithm = None

        for obj_name in self.objects:
            self.alg(obj_name)

    def alg(self, obj_name):
        """Instantiates an algorithm/object according to the
        global configuration and returns its instance."""

        if obj_name in self.algorithms:
            return self.algorithms[obj_name]

        else:
            obj = obj_name.split(":")[0]

            if obj in ["EVENT", "INPUT"]:
                return None

            elif obj in self.objects:

                obj_config = self.objects[obj]

                for m in sys.modules:

                    alg_name = m.split(".")[-1]

                    if obj_config["algorithm"] == alg_name:

                        module = importlib.import_module(m)

                        # algorithm instance.
                        self.algorithms[obj_name] = getattr(module, alg_name)(
                            obj_name, obj_config, self.store, self.logger
                        )

                        for _, output in self.algorithms[obj_name].output.items():

                            self.algorithms[output] = self.algorithms[obj_name]

                        return self.algorithms[obj_name]

                sys.exit(f"ERROR: object {obj} has requested a non-existing algorithm.")

            else:
                sys.exit(f"ERROR: object {obj} not defined in the configuration.")

    def launch(self):
        """Launches loops over inputs and outputs."""
        start = timeit.default_timer()

        msg = f"Launching pyrate run {self.name}"
        print("\n", "*" * len(msg), msg, "*" * len(msg))

        # -----------------------------------------------------------------------
        # Input loop.
        # -----------------------------------------------------------------------
        for i_name in tqdm(
            self.loaded_io["inputs"],
            desc="Input loop".ljust(70, "."),
            disable=self.no_progress_bar,
            bar_format=self.colors["blue"],
        ):

            self._current_input = self.loaded_io["inputs"][i_name]

            for self.state in ["initialise", "execute", "finalise"]:

                self.run()

            self._reset_algorithms_instance()

        # -----------------------------------------------------------------------
        # Output loop.
        # -----------------------------------------------------------------------
        for o_name in tqdm(
            self.loaded_io["outputs"],
            desc="Output loop".ljust(70, "."),
            disable=self.no_progress_bar,
            bar_format=self.colors["green"],
        ):

            self._current_output = self.loaded_io["outputs"][o_name]

            for t_name in self._current_output.targets:

                if not self.store.get(t_name) is EN.Pyrate.WRITTEN:

                    self._current_output.write(t_name)

        stop = timeit.default_timer()

        if self.no_progress_bar:
            print("Execution time: ", str(stop - start))

        # self.logger.info("Execution time: ", str(stop - start))
        return

    def run(self):
        """Run the loop function for the current state."""

        if self.state in ["initialise", "finalise"]:

            self.store.put("INPUT:name", self._current_input.name)

            self.store.put("INPUT:config", self._current_input.config)

            self.loop()

        elif self.state == "execute":

            tot_n_events = self._current_input.get_n_events()

            eslices = self.get_events_slices(tot_n_events)

            # ---------------------------------------------------------------
            # Event loop.
            # ---------------------------------------------------------------
            for emin, emax in eslices:

                info = (
                    "Event loop"
                    + f"({self._current_input.name},  emin: {emin},  emax: {emax})".rjust(
                        60, "."
                    )
                )

                self._current_input.set_idx(emin)

                erange = emax - emin + 1

                for idx in tqdm(
                    range(erange),
                    desc=f"{info}",
                    disable=self.no_progress_bar,
                    bar_format=self.colors["white"],
                ):
                    self.store.put("INPUT:name", self._current_input.name)

                    self.store.put("INPUT:config", self._current_input.config)

                    self.store.put("EVENT:idx", self._current_input.get_idx())

                    self.loop()

                    self._current_input.set_next_event()

    def loop(self):
        """Loop over targets and calls them."""
        self._reset_nodes_status()

        for t_name, t_instance in self.targets.items():

            if self._current_input.name in t_instance.job_inputs:

                self.call(t_name)

        self.store.clear()

    def call(self, obj_name):
        """Calls an algorithm for the current state."""

        node = self.node(obj_name)

        if not node.was_called:

            alg = node.algorithm

            if alg is not None:

                for condition, dependencies in alg.input.items():

                    for d in dependencies:
                        self.call(d)

                    passed = getattr(alg, self.state)(condition)

                    if not passed:
                        break

                # the block below is work in progress.
                # checking that the object is complete.
                # if not self.is_complete(obj_name, alg):
                #    sys.exit(
                #        f"ERROR: object {obj_name} is on the store but additional output is missing !!!"
                #    )

            else:
                self._current_input.read(obj_name)

            node.was_called = True

    # for o_name in self.node(obj_name).job_outputs:
    #
    #    if self.store.status(obj_name) is EN.Pyrate.READY:
    #
    #        self._current_output = self.loaded_io["outputs"][o_name]
    #
    #        self._current_output.write(obj_name)

    # def is_complete(self, obj_name, alg):
    #    """If the main object is on the store with a valid value,
    #    additional output is checked to be on the store."""
    #
    #    if self.store.get(obj_name) is not EN.Pyrate.NONE:
    #
    #        return all(
    #            [
    #                self.store.get(o) is not EN.Pyrate.NONE
    #                for o in alg.output[obj_name]
    #            ]
    #        )
    #
    #    else:
    #        return True

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
