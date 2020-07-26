""" This class will handle a set of configurations 
and launch several instances of a Run homogeneous
in purpose and structure.
"""
import os
import yaml
from itertools import groupby

from utils import strings as ST
from utils import functions as FN

from pyrate.core.Run import Run

class Job:
    def __init__(self, config):
        self.config = config

    def setup(self):
        """ Initialise 'private' configuration members.
        """
        
        self.inputs = {}
        for name,attr in self.config["inputs"].items():
            
            # This dictionary contains all input information. The file list contains lists 
            # which can have more than one element in the case of multiple channels declared in the group.
            self.inputs[name] = {"files":[]}
            
            # Find all relevant files using the list of paths and filtering with the sample and channel tags.
            for f in FN.find_files(attr["path"]): self.inputs[name]["files"].extend(f for s in ST.get_items(attr["samples"]) if s in f 
                            and FN.modus_ponens( FN.has_key("group",attr), any(c in f for c in ST.get_items(attr.get("group",False)))))
            
            # Group files using the first part of their names.
            self.inputs[name]["files"] = [list(f) for j, f in groupby(self.inputs[name]["files"], lambda a: a.partition("_")[0])]
            
            # Add all remaining attributes.
            self.inputs[name].update(attr)

        self.configs   = {}
        for name,attr in self.config["configs"].items():
            
            self.configs[name] = {"files":[]}
            
            for f in FN.find_files(attr["path"]): self.configs[name]["files"].extend(f for n in ST.get_items(attr["names"]) if n in f and f.lower().endswith(".yaml"))
            
            for f in self.configs[name]["files"]: self.configs[name].update(yaml.full_load(open(f,"r")))
         
        self.outputs   = {}
        for name,attr in self.config["outputs"].items():

            self.outputs[name] = {"files":[]}
            
            self.outputs[name]["files"] = os.path.join(attr["path"],name)

            self.outputs[name].update(attr)

        
        #self.use_nodes = self.config["use_nodes"] 


    def load(self):
        """ Initialise Run objects.
        """
        #run = Run(name = "TEST")
        pass



    def load(self):
        """ Initialise Run objects.
        """
        #run = Run(name = "TEST")
        pass

    def launch(self):
        #for k,v in self.config.items():
        #    print(k,v)
        #self.load() 
        self.setup() 


