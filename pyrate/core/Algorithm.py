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
        if self._input == {}:
            return {None: ""}
        return self._input

    @input.setter
    def input(self, config_input):
        """Setter method for input objects."""
        if self._input == {}:

            for dependency in FN.get_nested_values(config_input):

                if not isinstance(dependency, list):

                    variables = set(ST.get_items(str(dependency)))

                    self._update_input(None, variables)

                else:
                    for string in dependency:

                        for condition, variables in self.parse_input(string).items():

                            self._update_input(condition, variables)

    def _update_input(self, condition, variables):
        """Add condition and variables to the _input dictionary."""
        if "" in variables:
            variables.remove("")

        if not condition in self._input:
            self._input[condition] = variables
        else:
            self._input[condition].update(variables)

    def parse_input(self, s):
        """Returns a dictionary where keys are dependency conditions and values
        are the variables associated to them."""
        return {None: set()}

    @property
    def output(self):
        """Getter method for output objects."""
        return self._output

    @output.setter
    def output(self, config_output):
        """Setter method for output objects."""
        if self._output == {}:
            self._output = config_output


# EOF
