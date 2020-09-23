""" This class controls the execution of algorithms
    as a single local instance. 
"""
import sys
import importlib
import timeit
import time
import logging

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
        """Refining the input configuration."""
        # -----------------------------------------------------------------------
        # At this point the Run object should have self.input/config/output
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------
        self.state = None
        self._in = None
        self._out = None
        self._config = self.configs["global"]["objects"]

        fileHandler = logging.FileHandler(
            f"{self.name}.{time.strftime('%Y-%m-%d-%Hh%M')}.log", mode="w"
        )
        fileHandler.setFormatter(
            logging.Formatter("[%(asctime)s %(name)-16s %(levelname)-7s]  %(message)s")
        )

        self.logger.addHandler(fileHandler)

    def launch(self):
        """Implement input/output loop."""
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        store = Store(self)

        # -----------------------------------------------------------------------
        # Initialise/load the output. Files are opened and ready to be written.
        # -----------------------------------------------------------------------

        self._out = Output(self.name, store, self.logger, outputs=self.outputs)
        self._out.load()

        self.modify_config()

        # sys.exit()

        # -----------------------------------------------------------------------
        # Initialise algorithms for the declared object in the output.
        # -----------------------------------------------------------------------

        self.algorithms = {}
        for t in self._out.targets:
            self.add(self._config[t]["algorithm"]["name"], store, self.logger)

        start = timeit.default_timer()

        # -----------------------------------------------------------------------
        # Update the store in three steps: initialise, execute, finalise.
        # -----------------------------------------------------------------------

        store = self.run("initialise", store)

        if not store.check("any", "READY"):
            store = self.run("execute", store)

        store = self.run("finalise", store)

        # -----------------------------------------------------------------------
        # Write finalised objects to the output.
        # -----------------------------------------------------------------------

        for t in self._out.targets:
            self._out.write(t)

        stop = timeit.default_timer()

        print("Time: ", stop - start)

        return store

    def run(self, state, store):
        """Run the loop function."""
        self.state = state

        if self.state in ["initialise", "execute"]:
            for name, attr in self.inputs.items():
                self._in = Input(name, store, self.logger, attr)
                self._in.load()

                # The current input attribute dictionary is put on the transient store
                store.put("current_input", {"name": name, "attr": attr}, replace=True)

                if self.state in ["execute"]:
                    while self._in.next_event() >= 0:
                        self.loop(store, self._out.targets)

                else:
                    self.loop(store, self._out.targets)

        elif self.state in ["finalise"]:
            print("finalise")

            store.clear("READY")
            self.loop(store, self._out.targets)

        return store

    def loop(self, store, objects):
        """Loop over required objects to resolve them. Skips completed ones."""
        for obj_name in objects:
            if not store.check(obj_name, "READY"):
                self.call(obj_name)

        store.clear("TRAN")

    def call(self, obj_name):
        """Calls an algorithm."""
        self.add_name(obj_name, self._config[obj_name])
        getattr(
            self.algorithms[self._config[obj_name]["algorithm"]["name"]], self.state
        )(self._config[obj_name])

    def add_name(self, obj_name, config):
        """Adds name of object to its configuration."""
        if not "name" in config:
            config["name"] = obj_name

    def add(self, alg_name, store):
        """Adds instances of algorithms dynamically."""
        if not alg_name in self.algorithms:
            self.algorithms.update(
                {
                    alg_name: getattr(importlib.import_module(m), m.split(".")[-1])(
                        alg_name, store, self.logger
                    )
                    for m in sys.modules
                    if alg_name in m
                }
            )

    def update(self, obj_name, store):
        """Updates value of object on the store."""
        try:
            self.call(obj_name)

        except KeyError:
            pass

        try:
            self.add(self._config[obj_name]["algorithm"]["name"], store)
            self.call(obj_name)

        except KeyError:
            self._in.read(obj_name)

    def modify_config(self):
        """Modify original object configuration according to requirements in the job configuration."""
        intersection = {}
        for w_name, w in self._out.writers.items():
            if hasattr(w, "w_targets"):
                for wt in w.w_targets:
                    l = wt.split(":")
                    obj_name = l[0]

                    o = FN.nested(l)[obj_name]
                    c = self._config[obj_name]["algorithm"]
                    i = FN.intersect(o, c)

                    if obj_name not in intersection:
                        intersection[obj_name] = {}

                    intersection[obj_name] = FN.merge(intersection[obj_name], i)

        for t in self._out.targets:
            c = self._config[t]["algorithm"]
            c.update(intersection[t])


# EOF
