""" This class controls the execution of algorithms
    as a single local instance. 
"""
#import inspect

import sys
import importlib

import timeit

import pyrate.variables
import pyrate.trees
import pyrate.plots
import pyrate.histograms

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
        
        self.required_config = {}  
        required_objects = FN.flatten([[o for o in attr["objects"]] for name, attr in self.outputs.items()])

        print(required_objects)

        self.algorithms = {}
        for r in required_objects:
            self.add(self.objconfigs[r]["algorithm"]["name"], store)
        
        #print(algorithms)
        
        self.loop(store, required_objects, "initialise")


        #self.assign_config(required_objects)
        #"""
        start = timeit.default_timer()
        
        self.input_inst = {}
        for name, attr in self.inputs.items():
            I = Input(name, attr)
            I.load()
            self.input_inst["current"] = I

            h = I.get_object("PMT1_charge_waveform_muon") 

            while I.get_next_event() >= 0:
                pass
 
        stop = timeit.default_timer()
        
        print('Time: ', stop - start)  
        #"""




        """ 
        self.objorder = {}
        for o in required_objects:
            self._build_chain(o.split(":")[0])
        """ 
        
        #pretty(self.objorder)


        #print(self.store.algorithms)
        #for name, attr in self.inputs.items():
        #    self.inputs[name]["instance"] = Input(name, attr)
        #print(self.inputs)


    def loop(self, store, objects, state):
        """ Loop over required objects to resolve them. Skips completed ones.
        """
        store.set_state(state)
        for o in objects:
            if not store.get(o,"STATUS"):
                self.call(o, state) 


    def call(self, obj, state):
        """ Calls an algorithm.
        """
        self.add_name(obj, self.objconfigs[obj])
        print("Calling algorithm: ",self.objconfigs[obj]["algorithm"]["name"], state, "for object: ", obj)
        getattr(self.algorithms[self.objconfigs[obj]["algorithm"]["name"]], state)(self.objconfigs[obj])



    def check(self):
        """ Check if objects are ready.
        """
        pass



    def assign_config(self, objects):
        """ Modify configuration of object based on restricted selection in the job configuration.
        """
        
        modifications = [FN.nested(o.split(":")) for o in objects if ":" in o]

        print(modifications)

        newconfig = {}
        for d in modifications:
            k = list(d)[0]
            if not FN.has_key(k, newconfig): 
                newconfig[k] = d[k]
            else: 
                newconfig[k] = FN.merge(newconfig[k], d[k])
                #newconfig[k] =  newconfig[k] and d[k] 

        print(newconfig) 
        """ 
        for name, attr in newconfig.items():
            if name in self.objconfigs:
                self.objconfigs[name]["algorithm"] = FN.intersect(self.objconfigs[name]["algorithm"], attr)
                #FN.merge(self.objconfigs[name]["algorithm"], attr)
                #FN.merge(attr, self.objconfigs[name]["algorithm"])
                print()
                print()
                print(name, self.objconfigs[name]["algorithm"])
                print(name, attr)
                print()
                print()

        """ 

        


    def load(self):
        pass


    def launch(self):
        """ Implement input/output loop.
        """ 
        pass
    

    def add(self, name, store):
        """ Adds instances of algorithms dynamically.
        """
        if not name in self.algorithms:
            self.algorithms.update({name:getattr(importlib.import_module(m),m.split(".")[-1])(name, store) for m in sys.modules if name in m})
        print("This is the required name of alg: ", name)
        print(self.algorithms)
   


    def add_name(self, obj, config):
        """ Adds name of object to its configuration.
        """
        if not FN.has_key("name", config):
            config["name"] = obj




    def update(self, objname, store, state):
        """ Updates value of object on the store.
        """
        if objname in self.objconfigs:
            print("This is the objname", objname)
            print("This is the required algorithm", self.objconfigs[objname]["algorithm"]["name"])
            self.add(self.objconfigs[objname]["algorithm"]["name"], store)
            self.call(objname, state)

        else:
            print("Object not in configuration")



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








