""" This class controls the execution of algorithms
    as a single local instance. 
"""
import sys
import importlib
import timeit
import time
import logging

from colorama import Fore
from tqdm import tqdm

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

        self.colors = {"initialise": {}, "execute": {}, "finalise": {}}
        self.colors["initialise"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.BLUE,
            Fore.RESET,
        )
        self.colors["execute"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.YELLOW,
            Fore.RESET,
        )
        self.colors["execute"]["event"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.WHITE,
            Fore.RESET,
        )

    def launch(self):
        """Implement input/output loop."""
        # -----------------------------------------------------------------------
        # The store object is the output of the launch function.
        # -----------------------------------------------------------------------

        start = timeit.default_timer()

        store = Store(self)

        # -----------------------------------------------------------------------
        # Initialise/load the output. Files are opened and ready to be written.
        # -----------------------------------------------------------------------

        self._out = Output(self.name, store, self.logger, outputs=self.outputs)
        self._out.load()

        self.modify_config()

        # -----------------------------------------------------------------------
        # Initialise algorithms for the declared object in the output.
        # -----------------------------------------------------------------------

        self.algorithms = {}
        for t in self._out.targets:
            self.add(self._config[t]["algorithm"]["name"], store)

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

        # self.logger.info("Execution time: ", str(stop - start))

        return store

    def run(self, state, store):
        """Run the loop function."""
        self.state = state

        # -----------------------------------------------------------------------
        # Loop outer layer.
        # -----------------------------------------------------------------------
        if self.state in ["initialise", "execute"]:
            for name, attr in tqdm(
                self.inputs.items(),
                desc=f"Input loop: {self.state}",
                bar_format=self.colors[self.state]["input"],
            ):
                self._in = Input(name, store, self.logger, attr)
                self._in.load()

                # The current input specifications are put on the TRAN store.
                store.put("INPUT:name", name, replace=True)
                store.put("INPUT:config", attr, replace=True)

                # ---------------------------------------------------------------
                # Loop inner layer.
                # ---------------------------------------------------------------
                if self.state in ["execute"]:

                    for idx in tqdm(
                        range(self._in.get_n_events()),
                        desc=f"Event loop: {self.state}",
                        bar_format=self.colors[self.state]["event"],
                    ):
                        self.loop(store, self._out.targets)

                else:
                    self.loop(store, self._out.targets)

        elif self.state in ["finalise"]:

            store.clear("READY")
            store.clear("TRAN")
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
