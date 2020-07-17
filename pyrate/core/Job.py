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
        # list of outputs
        # list of algorithms
        # 
        
        self.inputs = {}
        for name,attr in self.config["inputs"].items():
            
            # This dictionary contains all input information. The file list 
            # contains lists which can have more than one element in the case 
            # of multiple channels declared in the group.
            self.inputs[name] = {"files":[]}
            
            # Find all relevant files using the list of paths and filtering with the sample and channel tags.
            for f in FN.find_files(attr["path"]): self.inputs[name]["files"].extend(f for s in ST.get_items(attr["samples"]) if s in f 
                    and FN.modus_ponens( FN.has_key("group",attr), any(c in f for c in ST.get_items(attr.get("group",False)))))
            
            # Group files using the first part of their names.
            self.inputs[name]["files"] = [list(f) for j, f in groupby(self.inputs[name]["files"], lambda a: a.partition("_")[0])]
            
            # Add all remaining attributes.
            self.inputs[name].update(attr)

    def load(self):
        #run = Run(name = "TEST")
        pass

    def launch(self):
        #for k,v in self.config.items():
        #    print(k,v)
        #self.load() 
        self.setup() 


