""" This class controls the execution of algorithms
    as a single local instance. 
"""

import sys
import time
import logging
import anytree.node.exceptions as anytreeExceptions

from anytree import Node

from colorama import Fore
from tqdm import tqdm

from pyrate.core.Store import Store

from pyrate.utils import functions as FN
from pyrate.utils import enums as EN

LONG_MAX = 2**64

class Run:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.input = None
        self.objects = None
        self.outputs = None

    def setup(self):
        """First instance of 'private' members."""        

        # -----------------------------------------------------------------------
        # At this point the Run object should have inputs/objects/outputs
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------

        log_file_name = f"{self.name}.{time.strftime('%Y-%m-%d-%Hh%M')}.log"

        # Will need to change handling of log files.

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
        # Only allow for one input - take the first input if given two
        self.input = [s for s in self.config["input"] if s != "event_start" and s != "event_num"][0]

        # ------------------------------------
        # Load the objects: algorithms / input
        # ------------------------------------
        self.objects = self.config["objects"]
        # Add the input to the objects list
        self.objects.update({self.input: self.config["input"][self.input]})
        self.nodes = {}
        self.variables = {}

        # instantiate all algorithms - even those not needed
        self.create_node(self.name)     # Create a run node
        for object_name in self.objects:
            self.create_node(object_name)

        # -----------------------------------------
        # Load the outputs and sort out dependecies
        # -----------------------------------------
        # Explicitly declare what variables the run will put on the store
        self.variables["EventNumber"] = self.name
        self.variables["EventTimestamp"] = self.name

        self.outputs = {}
        for output_name, output_config in self.config["outputs"].items():
            # Resolve all the dependecies
            targets = []
            for target in output_config["targets"]:
                # Search all the objects
                success = False
                for object_name, object_config in self.objects.items():
                    # Add all targets that match this algorithm name
                    if target == object_name or target == object_config["algorithm"]:
                        self.connect_node(object_name)
                        success = True
                        targets.append(object_name)
                if not success:
                    # This target couldn't be added
                    sys.exit(f"ERROR: in run {self.name}, target '{target}' doesn't match any of the objects in the loaded configs.")

            output_config["targets"] = targets
            OutputClass = FN.class_factory(output_config["algorithm"])
            self.outputs[output_name] = OutputClass(output_name, output_config, self.store, self.logger)

    def connect_node(self, obj_name):
        """Connects the already created nodes in the dependency chain
            Runs recursively
        """
        # Check if it's an input type or alg type
        if self.nodes[obj_name].algorithm is not None:
            # Check for children
            if not self.nodes[obj_name].children:
                for _, dependencies in self.nodes[obj_name].algorithm.input.items():
                    for d in dependencies:
                        try:
                            # Set this current node as the parent to the dependency
                            if d not in self.variables:
                                sys.exit(f"ERROR: variable '{d}' not found in the configurations or input variables.")
                            self.connect_node(self.variables[d]).parent = self.nodes[obj_name]
                        except anytreeExceptions.LoopError:
                            sys.exit(
                                f"ERROR: circular node detected between {d} and {obj_name}"
                            )

        # Return our finished node
        return self.nodes[obj_name]

    def _reset_node_called_status(self):
        """Resets all node's was_called flag"""
        for obj_name in self.nodes:
            self.nodes[obj_name].was_called = False

    def create_node(self, obj_name):
        """Instantiates an algorithm/object according to the
        global configuration and returns its instance."""
        # Node already exists, just return it
        if obj_name in self.nodes:
            return self.nodes[obj_name]

        # Create a new node
        new_node = Node(obj_name, algorithm=None, was_called=False)
        
        # Ignore things that get variables from the run itself
        if obj_name == self.name:
            self.nodes[obj_name] = new_node
            return

        if obj_name in self.objects:
            # Have to make the algorithm instance
            obj_config = self.objects[obj_name]
            algorithm_name = obj_config["algorithm"]
            AlgorithmClass = FN.class_factory(algorithm_name)
            new_node.algorithm = AlgorithmClass(obj_name, obj_config, self.store, self.logger)
            
            # Point all the alg outputs to the parent
            self.variables[obj_name] = obj_name
            for output in new_node.algorithm.output:
                self.variables[output] = obj_name
            
            self.nodes[obj_name] = new_node
            return

        sys.exit(f"ERROR: object '{obj_name}' not found in the configurations.")

    def run(self):
        """Launches loops over inputs and outputs."""
        msg = f"Launching pyrate run {self.name}"
        print("*" * len(msg), msg, "*" * len(msg))

        # ----------------------------------------------------------------------
        # Input loop.
        # ----------------------------------------------------------------------
        self.state = "initialise"
        self.store.put("INPUT:name", self.nodes[self.input].algorithm.name)
        self.store.put("INPUT:config", self.nodes[self.input].algorithm.config)
        self.loop()
        emin = self.config["input"]["event_start"]
        enum = self.config["input"]["event_num"]
        if emin > 0:
            # Skip the first emin events
            self.nodes[self.input].algorithm.skip_events(emin)

        # ---------------------------------------------------------------
        # Event loop.
        # ---------------------------------------------------------------
        def gen_execute():
            """ Custom dummy generator function for the execute loop to allow
                progress bar functionality
            """
            event_count = 0
            while self.nodes[self.input].algorithm.get_event():
                if enum > 0 and event_count >= enum:
                    break

                # Put the input info on the store
                self.store.put("INPUT:name", self.nodes[self.input].algorithm.name)
                self.store.put("INPUT:config", self.nodes[self.input].algorithm.config)
                self.store.put("EventNumber", event_count + emin)

                # Run all the algorithms
                self.loop()

                event_count += 1
                yield 1

        self.state = "execute"
        # tqdm iterator for the rate and timing
        sbar = tqdm(gen_execute(), position=0, leave=True)
        # tqdm progress bar
        bar_format = bar_format="{l_bar}{bar}|{n}/{total_fmt}% [{elapsed}<{remaining}]"
        pbar = tqdm(total=100, position=1, leave=True, bar_format=bar_format)
        count = 0
        prev_time = 0 # allows us to update with time
        for _ in sbar:
            # Update the bar every second
            if ((now:=time.time()) - prev_time) > 1:
                if enum < 0:
                    progress = self.nodes[self.input].algorithm.progress
                else:
                    progress = count / enum 
                pbar.n = round(progress * 100)
                pbar.refresh()
                prev_time = now
            count += 1
        pbar.n = 100    # set the bar to 100% complete
        pbar.refresh()

        # ----------------------------------------------------------------------
        # Output loop.
        # ----------------------------------------------------------------------
        
        self.state = "finalise"
        self.store.put("INPUT:name", self.nodes[self.input].algorithm.name)
        self.store.put("INPUT:config", self.nodes[self.input].algorithm.config)
        self.loop()

        for output in self.outputs:
            self.outputs[output].offload()

    def loop(self):
        """Loop over targets and calls them."""
        self._reset_node_called_status()
        for output in self.outputs:
            for target in self.outputs[output].targets:
                self.call(target, state=self.state)
        self.store.clear()

    def call(self, obj_name, state):
        """Calls an algorithm for the current state."""
        if obj_name == self.name:
            return
        node = self.nodes[obj_name]
        if not node.was_called:
            alg = node.algorithm

            if alg is not None:
                for condition, dependencies in alg.input.items():
                    for d in dependencies:
                        self.call(self.variables[d], state)
                    passed = getattr(alg, self.state)(condition)

                    if not passed:
                        break

            node.was_called = True

# EOF
