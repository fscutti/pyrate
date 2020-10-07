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
        """First instance of 'private' members."""
        # -----------------------------------------------------------------------
        # At this point the Run object should have self.input/config/output
        # defined after being read from the configuration yaml file.
        # -----------------------------------------------------------------------
        self.state = None
        self._in = None
        self._out = None
        self._config = self.configs["global"]["objects"]

        self._history = {}

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
        self.colors["finalise"]["input"] = "{l_bar}%s{bar}%s{r_bar}" % (
            Fore.GREEN,
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

        self.run_targets = self._out.get_targets()
        self.run_objects = self._out.get_objects()

        # self.modify_config()

        # -----------------------------------------------------------------------
        # Initialise algorithms for the declared object in the output.
        # -----------------------------------------------------------------------

        self.algorithms = {}
        for s, objects in self.run_targets.items():
            for o in objects:
                alg_name = self._config[o["config"]]["algorithm"]["name"]
                self.add(alg_name, store)

        # -----------------------------------------------------------------------
        # Update the store in three steps: initialise, execute, finalise.
        # -----------------------------------------------------------------------

        store = self.run("initialise", store)

        self.get_history(show=True)

        if not store.check("any", "READY"):
            store = self.run("execute", store)

        self.get_history(show=True)

        store = self.run("finalise", store)

        self.get_history(show=True)

        # -----------------------------------------------------------------------
        # Write finalised objects to the output.
        # -----------------------------------------------------------------------

        for obj_name in self.run_objects:
            self._out.write(obj_name)

        stop = timeit.default_timer()

        # self.logger.info("Execution time: ", str(stop - start))

        return store

    def run(self, state, store):
        """Run the loop function."""
        self.state = state

        if self.state in ["finalise"]:
            store.clear("READY")

        for i_name, objects in tqdm(
            self.run_targets.items(),
            desc=f"Input loop: {self.state}",
            bar_format=self.colors[self.state]["input"],
        ):

            if self.state in ["initialise", "execute"]:

                # The current input specifications are put on the TRAN store.
                store.put("INPUT:name", i_name, "PERM", replace=True)
                store.put("INPUT:config", self.inputs[i_name], "PERM", replace=True)

                self._in = Input(i_name, store, self.logger, self.inputs[i_name])
                self._in.load()

            if self.state == "initialise":
                # ---------------------------------------------------------------
                # Initialise
                # ---------------------------------------------------------------
                # To do: offload input at the end of loop?
                self.loop(store, self.run_targets[i_name])

                store.clear("TRAN")

            elif self.state == "execute":
                # ---------------------------------------------------------------
                # Execute
                # ---------------------------------------------------------------
                # To do: support event interval
                for idx in tqdm(
                    range(self._in.get_n_events()),
                    desc=f"Event loop: {self.state}",
                    bar_format=self.colors[self.state]["event"],
                ):
                    self.loop(store, self.run_targets[i_name])

                    store.clear("TRAN")

            elif self.state == "finalise":
                # ---------------------------------------------------------------
                # Finalise
                # ---------------------------------------------------------------
                for obj in objects:
                    if not store.check(obj["name"], "READY"):

                        self.loop(store, [obj])

                        if not store.check(obj["name"], "PERM"):
                            msg = f"finalise has been run for {obj['name']} but object has not been put on PERM store!!!"

                            sys.exit(f"ERROR: {msg}")
                            self.logger.error(msg)

                        else:
                            store.put(obj["name"], obj["name"], "READY")

        return store

    def loop(self, store, objects):
        """Loop over required objects to resolve them. Skips completed ones."""
        for obj in objects:

            self._history[obj["name"]] = []
            self._current_history = self._history[obj["name"]]

            self._config[obj["config"]]["name"] = obj["name"]

            if not store.check(obj["name"], "READY"):
                self.call(obj["config"], target_name=obj["name"])

    def call(self, obj_config, target_name="not a target"):
        """Calls an algorithm."""
        alg = self.algorithms[self._config[obj_config]["algorithm"]["name"]]

        entry = f"{obj_config}:{alg.name}:TARGET({target_name})"

        if entry in self._current_history:
            sys.exit(f"ERROR:{entry} already executed")
        else:
            getattr(alg, self.state)(self._config[obj_config])
            self._current_history.append(entry)

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

    def update(self, obj_config, store):
        """Updates value of object on the store."""
        try:
            self.call(obj_config)

        except KeyError:
            pass

        try:
            self.add(self._config[obj_config]["algorithm"]["name"], store)
            self.call(obj_config)

        except KeyError:
            self._in.read(obj_config)

    def get_history(self, show=False):
        """Returns the algorithm history."""
        if show:
            FN.pretty(self._history)
        return self._history

    """
    def modify_config(self):
        # Modify original object configuration according to requirements in the job configuration.
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
    """


# EOF
