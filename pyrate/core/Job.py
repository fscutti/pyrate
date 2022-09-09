""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

import os
import yaml
import glob

import pprint

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN

from pyrate.core.Run import Run


class Job:
    def __init__(self, name, config, log_level):
        self.name = name
        self.config = config
        self.log_level = log_level
        self.run = None

    def setup(self):
        """Instantiate Run objects."""
        # Input stuff
        # Pull out the event range
        input = self.config["input"]

        # Sort out the configs
        configs = []
        # Find all the config files
        for config in ST.read_list(self.config["configs"]):
            config = os.path.expandvars(config)
            configs += sorted(glob.glob(config))

        # Load all the config objects
        objects = {}
        for config in configs:
            config = yaml.full_load(open(config, "r"))
            objects.update(FN.expand_tags(config))
        objects = objects["objects"]

        # Outputs
        outputs = self.config["outputs"]
        for output_name in outputs:
            path = os.path.expandvars(outputs[output_name]["path"])
            outputs[output_name]["path"] = path

        run_config = {"input": input, "outputs": outputs, "objects": objects}
        self.run = Run(self.name, run_config)

    def launch(self):
        """Launch Run objects. """
        self.run.setup()
        self.run.run()

    def print_objects(self):
        """Prints out all objects"""
        pp = pprint.PrettyPrinter()
        pp.pprint(self.job["configs"]["global"]["objects"])


# EOF
