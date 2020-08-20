""" This class controls the execution of algorithms
    as a single local instance. 
"""
#import inspect

import pyrate.variables
import pyrate.trees
import pyrate.plots

from pyrate.core.Store import Store
from pyrate.core.Input import Input


class Run:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name

        
        #print(self.outputs)
        #print(self.configs)
        
    
    def setup(self):
        """ Instantiate relevant classes.
        """
        store = Store(name=self.name, run=self)
        self.objconfigs = self.configs["global"]["objects"]
        
        self.algorithms = {}
        for name, attr in self.outputs.items():
            for objname in attr["objects"]:
                if not self.objconfigs[objname]["algorithm"] in self.algorithms:
                    self.addalg(self.objconfigs[objname]["algorithm"], store)
        
        for name,attr in self.algorithms.items():
            attr.execute()

        print(self.store.algorithms)
        #for name, attr in self.inputs.items():
        #    self.inputs[name]["instance"] = Input(name, attr)
        #print(self.inputs)

    def load(self):
        pass


    def launch(self):
        """ Implement input/output loop.
        """
        pass
    
    def _unpack(self):
        pass
    

    def addalg(self, algname, store):
        """ Adds instances of algorithms dynamically.
        """
        if not algname in self.algorithms:
            self.algorithms.update({algname:getattr(importlib.import_module(m),m.split(".")[-1])(algname, store) for m in sys.modules if algname in m})


    def call(self, objname, store):
        if objname in self.objconfigs:
            if not self.objconfigs[objname]["algorithm"] in self.algorithms:
                self.addalg(self.objconfigs[objname]["algorithm"], store)
            store.objects[objname] = self.algorithms[self.objconfigs[objname]["algorithm"]].execute(SOME CONFIG)

            




