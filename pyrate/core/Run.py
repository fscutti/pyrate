""" This class controls the execution of algorithms
    as a single local instance. 
"""
import sys
import importlib
import timeit

import pyrate.variables
import pyrate.trees
import pyrate.plots
import pyrate.histograms

from pyrate.core.Store import Store
from pyrate.core.Input import Input
from pyrate.core.Output import Output

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Run:
    def __init__(self, name, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)
        self.name = name

    def setup(self):
        """ Instantiate relevant classes.
        """
        store = Store(name=self.name, run=self)
        self.obj_configs = self.configs["global"]["objects"]

        self.run_output = Output(self.name, store, self.outputs)
        self.run_output.load()

        #print(out)
        #sys.exit() 
        
        #self.required_config = {}  
        required_objects = FN.flatten([[o for o in attr["objects"]] for name, attr in self.outputs.items()])
        
        print(required_objects)

        self.algorithms = {}
        for t in self.run_output.targets:
            self.add(self.obj_configs[t]["algorithm"]["name"], store)
        
        #print(algorithms)
        

        start = timeit.default_timer()
        
        self.state = "initialise"
        
        self.run_input = None

        for name, attr in self.inputs.items():
            self.run_input = Input(name, store, attr)
            self.run_input.load()
            self.loop(store, required_objects)
        
            store.clear("TRAN")

        #self.assign_config(required_objects)
        #"""

        #print(self.run_input)
        
        #"""
        if not store.check("any","READY"):

            self.state = "execute"
            self.run_input = None
            for name, attr in self.inputs.items():
                self.run_input = Input(name, store, attr)
                self.run_input.load()
            
                while self.run_input.next_event() >= 0:
                    self.loop(store, required_objects)
                    store.clear("TRAN")
        
        # loop over output here!!!
        store.clear("READY")
        self.state = "finalise"
        self.loop(store, required_objects)
        #"""
        


        stop = timeit.default_timer()
        
        print('Time: ', stop - start)  
        #"""

        """ 
        self.objorder = {}
        for o in required_objects:
            self._build_chain(o.split(":")[0])
        """ 
        
        #FN.pretty(self.objorder)


        #print(self.store.algorithms)
        #for name, attr in self.inputs.items():
        #    self.inputs[name]["instance"] = Input(name, attr)
        #print(self.inputs)


    def loop(self, store, objects):
        """ Loop over required objects to resolve them. Skips completed ones.
        """
        #store.set_state(state)
        for o in objects:
            if not store.check(o,"READY"):
                self.call(o) 


    def call(self, obj):
        """ Calls an algorithm.
        """
        self.add_name(obj, self.obj_configs[obj])
        print("Calling algorithm: ",self.obj_configs[obj]["algorithm"]["name"], self.state, "for object: ", obj)
        getattr(self.algorithms[self.obj_configs[obj]["algorithm"]["name"]], self.state)(self.obj_configs[obj])



    def assign_config(self, objects):
        """ Modify configuration of object based on restricted selection in the job configuration.
        """
        
        modifications = [FN.nested(o.split(":")) for o in objects if ":" in o]

        print(modifications)

        newconfig = {}
        for d in modifications:
            k = list(d)[0]
            if not k in newconfig: 
                newconfig[k] = d[k]
            else: 
                newconfig[k] = FN.merge(newconfig[k], d[k])
                #newconfig[k] =  newconfig[k] and d[k] 

        print(newconfig) 
        """ 
        for name, attr in newconfig.items():
            if name in self.obj_configs:
                self.obj_configs[name]["algorithm"] = FN.intersect(self.obj_configs[name]["algorithm"], attr)
                #FN.merge(self.obj_configs[name]["algorithm"], attr)
                #FN.merge(attr, self.obj_configs[name]["algorithm"])
                print()
                print()
                print(name, self.obj_configs[name]["algorithm"])
                print(name, attr)
                print()
                print()

        """ 

        
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
        if not "name" in config:
            config["name"] = obj



    def update(self, obj_name, store):
        """ Updates value of object on the store. 
            To Do: possibly enforce the presence of objects on the store
            at this stage before calling the algorithm. Although this might
            slow things down.
        """
        try:
            self.call(obj_name)

        except KeyError:
            pass

        try:
            self.add(self.obj_configs[obj_name]["algorithm"]["name"], store)
            self.call(obj_name)

        except KeyError:
            print("This is a call to current input: ", obj_name)
            self.run_input.get_object(obj_name)
            #sys.exit()

    """
    def _build_chain(self, obj_name):
        
        while not obj_name in self.objorder:
            
            if "dependency" in self.obj_configs[obj_name]:
                objs = FN.flatten([ST.get_items(attr) for name, attr in self.obj_configs[obj_name]["dependency"].items()])
                
                if all([o in self.objorder for o in objs]):
                    self.objorder[obj_name] = self.obj_configs[obj_name] 
                
                else:
                    for o in objs:
                        self._build_chain(o)
            
            elif not obj_name in self.objorder: 
                self.objorder[obj_name] = self.obj_configs[obj_name] 
            
            else: print("ERROR")
    """








