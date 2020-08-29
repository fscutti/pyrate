""" This class controls the execution of algorithms
    as a single local instance. 
"""
#import inspect

import pyrate.variables
import pyrate.trees
import pyrate.plots

from pyrate.core.Store import Store
from pyrate.core.Input import Input

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


def pretty(d, indent=0):
    """ This function is just for testing purposes.
    """
    for key, value in d.items():
       print('\t' * indent + str(key))
       if isinstance(value, dict):
          pretty(value, indent+1)
       else:
          print('\t' * (indent+1) + str(value))



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
        
        """ 
        required_objects = FN.flatten([[o for o in attr["objects"]] for name, attr in self.outputs.items()])
        
        self.objorder = {}
        for o in required_objects:
            self._build_chain(o.split(":")[0])
        """ 
        
        #pretty(self.objorder)

        """
        algorithms = {}
        for name, attr in self.outputs.items():
            for objname in attr["objects"]:
                if not self.objconfigs[objname]["algorithm"] in algorithms:
                    self.add(self.objconfigs[objname]["algorithm"], algorithms, store)
        
        for name,attr in self.algorithms.items():
            attr.execute()
        """

        #print(self.store.algorithms)
        #for name, attr in self.inputs.items():
        #    self.inputs[name]["instance"] = Input(name, attr)
        print(self.inputs)

    
        for name, attr in self.inputs.items():
            I = Input(name, attr)
            I.load()
            
            while I.get_next_event() >= 0:
                pass
            print(I.get_ev_idx())
    
    def load(self):
        pass


    def launch(self):
        """ Implement input/output loop.
        """ 
        pass
    

    def add(self, name, algorithms, store):
        """ Adds instances of algorithms dynamically.
        """
        if not name in algorithms:
            algorithms.update({name:getattr(importlib.import_module(m),m.split(".")[-1])(name, store) for m in sys.modules if name in m})


    """
    def _build_chain(self, objname):
        
        while not objname in self.objorder:
            
            if "dependency" in self.objconfigs[objname]:
                objs = FN.flatten([ST.get_items(attr) for name, attr in self.objconfigs[objname]["dependency"].items()])
                
                if all([o in self.objorder for o in objs]):
                    self.objorder[objname] = self.objconfigs[objname] 
                
                else:
                    for o in objs:
                        self._build_chain(o)
            
            elif not objname in self.objorder: 
                self.objorder[objname] = self.objconfigs[objname] 
            
            else: print("ERROR")
    """


    def call(self, objname, store):
        pass
        """
        if objname in self.objconfigs:
            if not self.objconfigs[objname]["algorithm"] in self.algorithms:
                self.addalg(self.objconfigs[objname]["algorithm"], store)
            store.objects[objname] = self.algorithms[self.objconfigs[objname]["algorithm"]].execute(SOME CONFIG)
        """

            




























