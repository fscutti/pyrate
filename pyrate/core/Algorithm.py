""" Algorithm class.
"""

"""
*************************************************************
self.name is the name of the object you want to compute.
self.config is the configuration dictionary as in .yaml files

To define algorithms override at least one among:
   * initialise
   * execute 
   * finalise

At initialise you implicitly 'put' on the PERM store.
At execute you implicitly 'put' on the TRAN store.
At finalise you implicitly 'put' on the PERM store.

The 'get' method looks across all stores at all states.

*************************************************************
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums


class Algorithm:
    __slots__ = ["name", "config", "store", "logger", "time"]

    def __init__(self, name, config, store, logger):
        self.name = name
        self.config = config
        self.store = store
        self.logger = logger
        self.time = 0

    def initialise(self):
        """At this stage the method knows the current input."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def execute(self):
        """At this stage the method knows the current input and current event."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def finalise(self):
        """At this stage the method knows the current input."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def _prepare_input(self, state):
        """Prepares objects on the store before the execution of the state methods."""
        for o in self.config["dependency"][state]:
            self.store.get(o)

    def _initialise(self):
        """Do not override this method!"""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("initialise")

    def _execute(self):
        """Do not override this method!"""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("execute")

    def _finalise(self):
        """Do not override this method!"""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("finalise")


# EOF
