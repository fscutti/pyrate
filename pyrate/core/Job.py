""" This class will handle a set of configurations and launch several 
instances of a Run homogeneous in purpose and structure.
"""

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
        self.runs = []

    def setup(self):
        """Instantiate Run objects."""
        # Input stuff
        # Pull out the event range
        input = self.config["input"]
        run_name = [s for s in list(self.config["input"].keys()) if s != "event_range"][0]

        # Sort out the configs
        configs = []
        # Find all the config files
        for config in ST.read_list(self.config["configs"]):
            config = FN.find_env(config, env="PYRATE")
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
            path = FN.find_env(outputs[output_name]["path"])
            outputs[output_name]["path"] = path

        self.runs.append(Run(run_name, input=input, outputs=outputs, objects=objects, 
                             config=self.config))

    def launch(self):
        """Launch Run objects. """
        for r in self.runs:
            r.setup()
            r.launch()

    def print_objects(self):
        """Prints out all objects"""
        pp = pprint.PrettyPrinter()
        pp.pprint(self.job["configs"]["global"]["objects"])


# EOF
