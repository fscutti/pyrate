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
    __slots__ = ["name", "config", "store", "logger", "_input", "_output"]

    def __init__(self, name, config, store, logger):
        self.name = name
        self.config = config
        self.store = store
        self.logger = logger

        self._input = {}
        self._output = {}

    def initialise(self, condition=None):
        """At this stage the method knows the current input."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def execute(self, condition=None):
        """At this stage the method knows the current input and current event."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def finalise(self, condition=None):
        """At this stage the method knows the current input."""
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    @property
    def input(self):
        return self._input

    @input.setter
    def input(self, config):

        for i in FN.get_nested_values(config):

            if isinstance(i, str):
                for s in ST.get_items(i):
                    self._input[s] = None

            elif isinstance(i, list):
                for s, c in self.parse_input_string(i).items():
                    self._input[s] = c

    def parse_input_string(self, s):
        """Returns a dictionary.
        This function is reimplemented by derived algorithms."""
        return {}


# EOF
