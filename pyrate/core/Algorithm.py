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
        pass

    def execute(self, condition=None):
        """At this stage the method knows the current input and current event."""
        pass

    def finalise(self, condition=None):
        """At this stage the method knows the current input."""
        pass

    @property
    def input(self):
        """Getter method for input objects."""
        return self._input

    @input.setter
    def input(self, config_input):
        """Setter method for input objects."""
        for i in FN.get_nested_values(config_input):

            if isinstance(i, str):
                for s in ST.get_items(i):
                    self._input[s] = None

            elif isinstance(i, list):
                for s, c in self.parse_input(i).items():
                    self._input[s] = c

    def parse_input(self, l=[]):
        """Returns a dictionary where keys are dependencies
        and values are conditions to be evaluated by the Algorithm.
        This function is reimplemented by derived algorithms."""
        return {}

    @property
    def output(self):
        """Getter method for output objects."""
        return self._output

    @output.setter
    def output(self, config_output):
        """Setter method for output objects."""
        self._output[self.name] = [f"{self.name}:{o}" for o in ST.get_items(config_output)]


# EOF
