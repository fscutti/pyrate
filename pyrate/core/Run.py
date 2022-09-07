""" This class controls the execution of algorithms
    as a single local instance. 
"""

import sys
import timeit
import time
import logging
import anytree.node.exceptions as anytreeExceptions

from anytree import Node

from colorama import Fore
from tqdm import tqdm

from pyrate.core.Store import Store
from pyrate.core.Output import Output

from pyrate.utils import functions as FN
from pyrate.utils import enums as EN


class Run:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.input = None
        self.outputs = []
        self.objects = None

    def setup(self):
        """First instance of 'private' members."""        

        # -----------------------------------------------------------------------
        # At this point the Run object should have inputs/objects/outputs
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

        # -------------------
        # Load the input name
        # -------------------
        self.input = [s for s in self.config["input"] if s != "event_start" and s != "event_num"][0]
        
        # -------------------------------------
        # Load the objects / algorithms / input
        # -------------------------------------
        self.objects = self.config["objects"]
        # Add the input to the objects list
        self.objects.update({self.input: self.config["input"][self.input]})
        self.targets, self.nodes, self.algorithms, self.readers = {}, {}, {}, {}
        
        # instantiate all algorithms - even those not needed
        for obj_name in self.objects:
            self.alg(obj_name)

        # -----------------------------------------
        # Load the outputs and sort out dependecies
        # -----------------------------------------
        for output_name, output_config in self.config["outputs"].items():
            output = Output(output_name, output_config, self.store, self.logger)
            output.load()

            # Resolve all the dependecies
            for target in output.targets:
                if target not in self.targets:
                    self.targets[target] = self.node(target)

    def node(self, obj_name):
        """Instantiates a node for an object, including the corresponding algorithm instance
        and the list of relevant samples. This function checks for circular dependencies.
        The node instance is returned. This is a recursive function."""

        # this call is necessary to find the correct algorithm for secondary outputs.
        # N.B.: all object calls first pass through the node function.

        # Node already exists, just return it
        if obj_name in self.nodes:
            return self.nodes[obj_name]

        # Create a new node
        new_node = Node(obj_name, algorithm=None, was_called=False)

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

    def _reset_node_called_status(self):
        """Resets all node's was_called flag"""
        for obj_name in self.nodes:

            self.nodes[obj_name].was_called = False

    def alg(self, obj_name):
        """Instantiates an algorithm/object according to the
        global configuration and returns its instance."""
        if obj_name in self.algorithms:
            # Found it already, just return it
            return self.algorithms[obj_name]

        if obj_name in self.objects:
            # Have to make the algorithm instance
            obj_config = self.objects[obj_name]
            algorithm_name = obj_config["algorithm"]
            AlgorithmClass = FN.get_class(algorithm_name)
            self.algorithms[obj_name] = AlgorithmClass(obj_name, obj_config, self.store, self.logger)
            
            # Point all the alg outputs to the parent
            for _, output in self.algorithms[obj_name].output.items():
                self.algorithms[output] = self.algorithms[obj_name]
            
            return self.algorithms[obj_name]

        # sys.exit(f"ERROR: object '{obj_name}' not found in the configurations.")

    def run(self):
        """Launches loops over inputs and outputs."""
        start = timeit.default_timer()
        # msg = f"Launching pyrate run {self.name}"
        # print("\n", "*" * len(msg), msg, "*" * len(msg))

        # ----------------------------------------------------------------------
        # Input loop.
        # ----------------------------------------------------------------------
        self.state = "initialise"
        self.store.put("INPUT:name", self.algorithms[self.input].name)
        self.store.put("INPUT:config", self.algorithms[self.input].config)
        self.loop()

        # est_nevents = self._current_input.get_n_events()
        emin = self.config["input"]["event_start"]
        enum = self.config["input"]["event_num"]
        if emin > 0:
            # Skip the first emin events
            self.input.skip_events(emin)

        # ---------------------------------------------------------------
        # Event loop.
        # ---------------------------------------------------------------
        def generator():
            """ Custom dummy generator function for the execute loop to allow
                progress bar functionality
            """
            event_count = 0
            while self.algorithms[self.input].get_event():
                # print(f"{self.algorithms[self.input].progress=}")
                if enum > 0 and event_count > enum:
                    break

                # Put the input info on the store
                self.store.put("INPUT:name", self.algorithms[self.input].name)
                self.store.put("INPUT:config", self.algorithms[self.input].config)
                self.store.put("EVENT:idx", event_count + emin)

                # Run all the algorithms
                self.loop()

                event_count += 1
                yield

        self.state = "execute"
        # with tqdm() as pbar:
        #     count = 0
        #     for _ in generator():
        #         if (count % 1000) == 0:
        #             progress = self.algorithms[self.input].progress
        #             pbar.n = round(progress * 100)
        #             pbar.refresh()
        #         count += 1
        #     pbar.n = 100
        #     pbar.refresh()
        
        for _ in tqdm(generator()): pass

        # ----------------------------------------------------------------------
        # Output loop.
        # ----------------------------------------------------------------------
        self.state = "finalise"
        self.store.put("INPUT:name", self.algorithms[self.input].name)
        self.store.put("INPUT:config", self.algorithms[self.input].config)
        # getattr(self.input, self.state)()
        self.loop()

        for output in self.outputs:
            for target in output.targets:
                if not self.store.get(target) is EN.Pyrate.WRITTEN:
                    output.write(target)

        stop = timeit.default_timer()
        print(f"Execution time: {stop - start:.2f}s")

        return

    def loop(self):
        """Loop over targets and calls them."""
        self._reset_node_called_status()
        for target in self.targets:
            self.call(target, state=self.state)
        self.store.clear()

    def call(self, obj_name, state):
        """Calls an algorithm for the current state."""
        node = self.node(obj_name)
        if not node.was_called:
            alg = node.algorithm

            if alg is not None:
                for condition, dependencies in alg.input.items():
                    for d in dependencies:
                        self.call(d, state)
                    passed = getattr(alg, self.state)(condition)

                    if not passed:
                        break

            node.was_called = True

# EOF
