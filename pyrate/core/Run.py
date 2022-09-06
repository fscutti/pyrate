""" This class controls the execution of algorithms
    as a single local instance. 
"""
import os
import sys
import yaml
import pkgutil
import importlib
import timeit
import time
import logging
import anytree.node.exceptions as anytreeExceptions

from anytree import Node

from colorama import Fore
from tqdm import tqdm

from pyrate.core.Store import Store
from pyrate.core.EventBuilder import EventBuilder
from pyrate.readers.ReaderCAEN1730_PSD import ReaderCAEN1730_PSD
from pyrate.core.Output import Output

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums as EN


class Run:
    def __init__(self, name, input, outputs, objects, config):
        self.name = name
        self.config = config
        self.event_range = input["event_range"]
        del input["event_range"]
        self.input_config = input
        self.input = None
        self.output_configs = outputs
        self.outputs = []
        self.objects = objects

    def setup(self):
        """First instance of 'private' members."""        

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
        
        # Set the run state and create the store
        self.state = None
        self.store = Store(self.name)

        # Loading the input for this run
        input_name, input_config = list(self.input_config.items())[0]
        for r in sys.modules:
            if input_config["algorithm"] == r.split(".")[-1]:
                self.input = getattr(importlib.import_module(r), input_config["algorithm"])(
                    input_name, input_config, self.store, self.logger)
                break
        # input_name, input_config = list(self.input_config.items())[0]
        # input_modules = {}
        # core_modules = {name: f"pyrate.core.{name}" for _, name, _ in pkgutil.iter_modules(["pyrate/core"])}
        # reader_modules = {name: f"pyrate.readers.{name}" for _, name, _ in pkgutil.iter_modules(["pyrate/readers"])}
        # input_modules.update(core_modules)
        # input_modules.update(reader_modules)
        # for module_name, module_path in input_modules.items():
        #     if module_name == input_config["algorithm"]:
        #         print("Hi")
        #         try:
        #             InputModule = importlib.import_module(module_path)
        #             InputClass = InputModule.__getattribute__(module_name)
        #             self.input = InputClass(input_name, input_config, self.store, self.logger)
        #             break
        #         except ImportError as err:
        #             sys.exit(
        #                 f"ERROR: {err}\n Unable to import input '{input_name}' from module '{module_name}'\n"
        #                 "Check that the reader is in pyrate/readers, that the class and module have the same name, and is added the nearest __init__.py"
        #             )
        
        self.targets, self.nodes, self.algorithms, self.readers = {}, {}, {}, {}
        # instantiate all algorithms - even those not needed.
        self._reset_algorithms_instance()

        # from this line on there will be major restructurings
        # one can eliminate targets.

        for output_name, output_config in self.output_configs.items():
            output = Output(output_name, output_config, self.store, self.logger)
            output.load()

            for target in output.targets:
                if target not in self.targets:
                    self.targets[target] = self.node(target)

        # initialising job inputs / outputs for the targets.
        # REMOVE ME
        for target in self.targets:
            if self.node(target).job_inputs == []:
                self.node(target).job_inputs = self.input

    def node(self, obj_name, job_inputs=[]):
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
        )

        # Get the algorithm
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

        # ----------------------------------------------------------------------
        # Input loop.
        # ----------------------------------------------------------------------
        for self.state in ["initialise", "execute", "finalise"]:

            self.run()

        self._reset_algorithms_instance()

        # ----------------------------------------------------------------------
        # Output loop.
        # ----------------------------------------------------------------------

        for output in tqdm(
            self.outputs,
            desc="Output loop".ljust(70, "."),
            disable=self.config["no_progress_bar"],
            bar_format=self.colors["green"],
        ):

            for target in output.targets:
                if not self.store.get(target) is EN.Pyrate.WRITTEN:
                    output.write(target)

        stop = timeit.default_timer()

        if self.config["no_progress_bar"]:
            print("Execution time: ", str(stop - start))

        return

    def run(self):
        """Run the loop function for the current state."""

        if self.state in ["initialise", "finalise"]:

            self.store.put("INPUT:name", self.input.name)

            self.store.put("INPUT:config", self.input.config)

            getattr(self.input, self.state)()

            self.loop()

        elif self.state == "execute":

            # est_nevents = self._current_input.get_n_events()
            emin = self.event_range[0]
            if emin > 0:
                # Skip the first emin events
                self.input.skip_events(emin)
            emax = self.event_range[1]

            # ---------------------------------------------------------------
            # Event loop.
            # ---------------------------------------------------------------
            event_n = emin
            while self.input.get_event():
                if emax > 0 and event_n > emax:
                    break

                # Put the input info on the store
                self.store.put("INPUT:name", self.input.name)
                self.store.put("INPUT:config", self.input.config)
                self.store.put("EVENT:idx", event_n)

                # Run all the algorithms
                self.loop()

                event_n += 1
                
                # info = (
                #     "Event loop"
                #     + f"({self._current_input.name},  emin: {emin},  emax: {emax})".rjust(
                #         60, "."
                #     )
                # )         

    def loop(self):
        """Loop over targets and calls them."""
        self._reset_nodes_status()

        for target in self.targets:
            self.call(target)

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

            else:
                pass
                # self.input.get_event(obj_name)

            node.was_called = True

# EOF
