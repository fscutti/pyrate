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
        if self._input == {}:

            dependencies = FN.get_nested_values(config_input)

            conditional, unconditional = {}, {}

            for i in dependencies:

                if isinstance(i, list):
                    conditional.update({v: c for v, c in self.parse_input(i).items()})

                elif isinstance(i, str):
                    unconditional.update({v: None for v in ST.get_items(i)})

            # the order of these update instructions matters, as for selection 
            # algorithms we might want to interrupt input evaluation if all 
            # conditional ones are satisfied.
            self._input.update(conditional)
            self._input.update(unconditional)
            
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
        if self._output == {}:

            self._output[self.name] = [
                f"{self.name}:{o}" for o in ST.get_items(config_output)
            ]


# EOF
