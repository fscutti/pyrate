""" This class will handle a set of configurations 
and launch several instances of a Run homogeneous
in purpose and structure.
"""
import os
from itertools import groupby, dropwhile

from utils import strings as ST
from utils import functions as FN

from pyrate.core.Run import Run

class Job:
    def __init__(self, config):
        self.config = config

    def setup(self):
        """ Initialise 'private' data members.
        """
        #self.build_run_config()  
        # list of outputs
        # list of algorithms
        # 
        
        inputs = {}
        for name,attr in self.config["inputs"].items():
            inputs[name] = {"files":[]}
            for f in FN.find_files(attr["path"]): inputs[name]["files"].extend(f for s in ST.get_items(attr["samples"]) if s in f 
                    and FN.modus_ponens( FN.has_key("group",attr), any(c in f for c in ST.get_items(attr.get("group",False)))))
            inputs[name]["files"] = [list(f) for j, f in groupby(inputs[name]["files"], lambda a: a.partition("_")[0])]


    def load(self):
        #run = Run(name = "TEST")
        pass

    def launch(self):
        #for k,v in self.config.items():
        #    print(k,v)
        #self.load() 
        self.setup() 


