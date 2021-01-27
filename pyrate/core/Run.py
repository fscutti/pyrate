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

        self._history = {"CURRENT TARGET": None}

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

        store.put("history", self._history, "PERM")

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
        for i_name, targets in self.run_targets.items():
            for t in targets:
                alg_name = self._config[t["config"]]["algorithm"]["name"]
                self.add(alg_name, store)

        # -----------------------------------------------------------------------
        # Inputs will be initialised dynamically in the run function.
        # -----------------------------------------------------------------------
        self.ready_inputs = {}

        # -----------------------------------------------------------------------
        # Update the store in three steps: initialise, execute, finalise.
        # -----------------------------------------------------------------------

        msg = f"Launching pyrate run {self.name}"

        print("\n")
        print("*" * len(msg))
        print(msg)
        print("*" * len(msg))

        store = self.run("initialise", store)

        if not store.check("any", "READY"):

            store = self.run("execute", store)

        store = self.run("finalise", store)

        print("\n")

        stop = timeit.default_timer()

        if self.no_progress_bar:
            print("Execution time: ", str(stop - start))

        # self.logger.info("Execution time: ", str(stop - start))

        return store

    def run(self, state, store):
        """Run the loop function."""

        prefix_types = {
            "initialise": "Inputs:  ",
            "execute": "Events:  ",
            "finalise": "Targets: ",
        }

        self.state = state

        prefix = prefix_types[state]

        info = self.state.rjust(70, ".")

        if self.state in ["finalise"]:
            store.clear("READY")

        for i_name, targets in tqdm(
            self.run_targets.items(),
            desc=f"{prefix}{info}",
            disable=self.no_progress_bar,
            bar_format=self.colors[self.state]["input"],
        ):

            if self.state in ["initialise", "execute"]:

                if not i_name in self.ready_inputs:
                    self.ready_inputs[i_name] = Input(
                        i_name, store, self.logger, self.inputs[i_name]
                    )

                self._in = self.ready_inputs[i_name]

                if not self._in.is_loaded:
                    self._in.load()

            if self.state == "initialise":
                # ---------------------------------------------------------------
                # Initialise
                # ---------------------------------------------------------------
                store.put("INPUT:name", i_name, "TRAN")
                store.put("INPUT:config", self.inputs[i_name], "TRAN")

                self.loop(store, self.run_targets[i_name])

                store.clear("TRAN")

            elif self.state == "execute":
                # ---------------------------------------------------------------
                # Execute
                # ---------------------------------------------------------------
                
                tot_n_events = self._in.get_n_events()

                eslices = self.get_events_slices(tot_n_events)
                
                # ---------------------------------------------------------------
                # Event loop
                # ---------------------------------------------------------------

                for emin, emax in eslices:

                    info = (
                        f"{self.state} ({i_name},  emin: {emin},  emax: {emax})".rjust(
                            70, "."
                        )
                    )
                    
                    self._in.set_idx(emin)

                    erange = emax - emin + 1

                    for idx in tqdm(
                        range(erange),
                        desc=f"{prefix}{info}",
                        disable=self.no_progress_bar,
                        bar_format=self.colors[self.state]["event"],
                    ):
                        store.put("INPUT:name", i_name, "TRAN")
                        store.put("INPUT:config", self.inputs[i_name], "TRAN")
                        store.put("EVENT:idx", self._in.get_idx())
                        

                        self.loop(store, self.run_targets[i_name])

                        store.clear("TRAN")

                        self._in.set_next_event()

                self._in.offload()

            elif self.state == "finalise":
                # ---------------------------------------------------------------
                # Finalise
                # ---------------------------------------------------------------
                for t in targets:
                    if not store.check(t["name"], "READY"):

                        self.loop(store, [t])

                        if not store.check(t["name"], "PERM"):
                            msg = f"finalise has been run for {t['name']} but object has not been put on PERM store!!!"

                            sys.exit(f"ERROR: {msg}")
                            self.logger.error(msg)

                        else:
                            store.put(t["name"], t["name"], "READY")
        
        if self.state in ["finalise"]:

            for o in self.run_objects:
                self._out.write(o)
                    
        return store

    def loop(self, store, targets):
        """Loop over required targets to resolve them. Skips completed ones."""
        for t in targets:

            self._history[t["name"]] = []
            self._target_history = self._history[t["name"]]

            self._history["CURRENT TARGET"] = t["name"]

            self._config[t["config"]]["name"] = t["name"]

            if not store.check(t["name"], "READY"):
                self.call(t["config"], is_target=t["name"])

    def call(self, obj_config, is_target=""):
        """Calls an algorithm."""

        # print(f"calling {obj_config} is target: ({is_target})")
        alg = self.algorithms[self._config[obj_config]["algorithm"]["name"]]
        entry = f"{obj_config}:{alg.name}:TARGET({is_target})"

        if not is_target:
            self._config[obj_config]["name"] = obj_config

        if entry in self._target_history:

            self.get_history(show=True)
            FN.pretty(self._config[obj_config])
            sys.exit(f"ERROR:{entry} already executed")
        else:
            self._target_history.append(entry)
            getattr(alg, self.state)(self._config[obj_config])

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
            return

        except KeyError:
            pass

        try:
            self.add(self._config[obj_config]["algorithm"]["name"], store)
            self.call(obj_config)
            return

        except KeyError:
            self._in.read(obj_config)
            return

    def get_history(self, show=False):
        """Returns the algorithm history."""
        if show:
            FN.pretty(self._history)
        return self._history

    def get_events_slices(self, tot):
        """Updates emin and emax attributes for running on valid slice."""

        eslices = []

        # ---------------------------------------------------------------
        # Reading input events
        # ---------------------------------------------------------------
        if hasattr(self._in, "eslices"):

            if isinstance(self._in.eslices, dict):
                emin, emax = 0, tot - 1

                if "emin" in self._in.eslices:
                    emin = self._in.eslices["emin"]

                if "emax" in self._in.eslices and self._in.eslices["emax"] > -1:
                    emax = self._in.eslices["emax"]

                eslices.append((emin, emax))

            elif isinstance(self._in.eslices, list):

                for s in self._in.eslices:

                    if "slice" in s:

                        s_nparts = int(s["nparts"])
                        s_slice = "all"

                        if not s["slice"] == "all":
                            s_slice = int(s["slice"])

                        part = int(tot / s_nparts)

                        emin, emax = 0, part - 1

                        for s_idx in range(s_nparts):

                            if not s_slice == "all":
                                if s_idx == s_slice - 1:

                                    if s_idx == s_nparts - 1:
                                        eslices.append((emin, tot - 1))
                                        break

                                    else:
                                        eslices.append((emin, emax))
                                        break

                            else:
                                if s_idx == s_nparts - 1:
                                    eslices.append((emin, tot - 1))
                                else:
                                    eslices.append((emin, emax))

                            emin += part
                            emax += part

                    else:
                        emin, emax = 0, tot - 1

                        if "emin" in s:
                            emin = s["emin"]

                        if "emax" in s and s["emax"] > -1:
                            emax = s["emax"]

                        eslices.append((emin, emax))

            else:
                emin, emax = 0, self._in.eslices - 1

                eslices.append((emin, emax))

        for emin, emax in eslices:
            self.check_events_slices(emin, emax, tot)

        return eslices

    def check_events_slices(self, emin, emax, tot):
        """Validate events slice."""

        if not emin <= emax <= tot - 1:
            sys.exit(
                f"ERROR: required input range not valid. emin:{emin} <= emax:{emax} <= {tot - 1}"
            )

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
