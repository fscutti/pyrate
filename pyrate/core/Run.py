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
        """ Refining the input configuration.
        """
        # -----------------------------------------------------------------------
        # At this point the Run object should have self.input/config/output 
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------
        self.state = None
        self._in = None
        self._out = None
        self._config = self.configs["global"]["objects"]

    def launch(self):
        """ Implement input/output loop.
        """ 
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        store = Store(self)

        # -----------------------------------------------------------------------
        # Initialise/load the output. Files are opened and ready to be written.
        # -----------------------------------------------------------------------

        self._out = Output(self.name, store, outputs=self.outputs)
        self._out.load()
        
        # -----------------------------------------------------------------------
        # Initialise algorithms for the declared object in the output.
        # -----------------------------------------------------------------------
        
        self.algorithms = {}
        for t in self._out.targets:
            self.add(self._config[t]["algorithm"]["name"], store)

        start = timeit.default_timer()
        
        # -----------------------------------------------------------------------
        # Update the store in three steps: initialise, execute, finalise.
        # -----------------------------------------------------------------------
        
        store = self.run("initialise", store)

        if not store.check("any","READY"):
            store = self.run("execute", store)

        store = self.run("finalise", store)
        
        # -----------------------------------------------------------------------
        # Write finalised objects to the output.
        # -----------------------------------------------------------------------

        for o in self._out.targets:
            self._out.write(o)

        stop = timeit.default_timer()
        
        print('Time: ', stop - start)  

        return store

    def run(self, state, store):
        """ Run the loop function.
        """
        self.state = state

        if self.state in ["initialise", "execute"]:
            for name, attr in self.inputs.items():
                self._in = Input(name, store, attr)
                self._in.load()

                # The current input is put on the transient store
                store.put("current_input", name, force=True)
                
                if self.state in ["execute"]:
                    while self._in.next_event() >= 0:
                        self.loop(store, self._out.targets)

                else: 
                    self.loop(store, self._out.targets)

        elif self.state in ["finalise"]:

            store.clear("READY")
            self.loop(store, self._out.targets)

        return store

    def loop(self, store, objects):
        """ Loop over required objects to resolve them. Skips completed ones.
        """
        for o in objects:
            if not store.check(o,"READY"):
                self.call(o) 
        
        store.clear("TRAN")

    def call(self, obj):
        """ Calls an algorithm.
        """
        self.add_name(obj, self._config[obj])
        getattr(self.algorithms[self._config[obj]["algorithm"]["name"]], self.state)(self._config[obj])
    
    def add_name(self, obj, config):
        """ Adds name of object to its configuration.
        """
        if not "name" in config:
            config["name"] = obj


    def add(self, name, store):
        """ Adds instances of algorithms dynamically.
        """
        if not name in self.algorithms:
            self.algorithms.update({name:getattr(importlib.import_module(m),m.split(".")[-1])(name, store) for m in sys.modules if name in m})

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
            self.add(self._config[obj_name]["algorithm"]["name"], store)
            self.call(obj_name)

        except KeyError:
            self._in.read(obj_name)

    def modify_config(self, objects):
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
            if name in self._config:
                self._config[name]["algorithm"] = FN.intersect(self._config[name]["algorithm"], attr)
                #FN.merge(self._config[name]["algorithm"], attr)
                #FN.merge(attr, self._config[name]["algorithm"])
                print()
                print()
                print(name, self._config[name]["algorithm"])
                print(name, attr)
                print()
                print()

        """ 
# EOF
