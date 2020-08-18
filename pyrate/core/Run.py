""" This class controls the execution of algorithms
    as a single local instance. 
"""
import sys
import inspect
import importlib

import pyrate.variables
import pyrate.trees
import pyrate.plots

from pyrate.core.Store import Store
from pyrate.core.Input import Input


#print(sys.modules.keys())

#print(inspect.getmembers(sys.modules["pyrate.plots.Plot1DROOT"]))
#print(inspect.getmembers(sys.modules["plots.Plot1DROOT"]))

#from pyrate.core.Input import Input
#from plots import Plot1DROOT

#print(inspect.getmodule("Input"))
#print(inspect.getmembers(pyrate))


class Run:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name

        
        #print(self.outputs)
        #print(self.configs)
        
    
    def setup(self):
        """ Instantiate relevant classes.
        """
        self.store = Store(name=self.name)
        self.algorithms = {}
        self.objconfigs = self.configs["global"]["objects"]
        
        for name, attr in self.outputs.items():
            for objname in attr["objects"]:
                if not objname in self.algorithms:
                    self._addalg(self.objconfigs[objname]["algorithm"])
        
        
        print(self.algorithms)
        #for name, attr in self.inputs.items():
        #    self.inputs[name]["instance"] = Input(name, attr)
        #print(self.inputs)

    def load(self):
        pass


    def launch(self):
        """ Implement input/output loop.
        """
        pass
    
    def unpack(self):
        pass
    
    def _addalg(self, algname):
        if not algname in self.algorithms:
            self.algorithms.update({algname:getattr(importlib.import_module(m),m.split(".")[-1])(algname,self.store) for m in sys.modules if algname in m})








