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
        for run_name, run_config in self.config["runs"].items():
            
            # Sort out the configs
            configs = []
            # Find all the config files
            for config in ST.read_list(run_config["configs"]):
                config = FN.find_env(config, env="PYRATE")
                configs += sorted(glob.glob(config))
            
            # load all the config objects
            objects = {}
            for config in configs:
                config = yaml.full_load(open(config, "r"))
                objects.update(FN.expand_tags(config))
            run_config["configs"] = configs

            self.runs.append(Run(run_name, config=run_config, inputs=run_config["inputs"], 
                                 outputs=run_config["outputs"], objects=objects["objects"]))

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
