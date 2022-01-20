""" Algorithm class.
"""

"""
*************************************************************
config['name'] is the name of the object you want to compute.
*************************************************************
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN
from pyrate.utils import enums


class Algorithm:
    __slots__ = ["name", "config", "store", "logger"]

    def __init__(self, name, config, store, logger):
        self.name = name
        self.config = config
        self.store = store
        self.logger = logger

    def initialise(self):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input.
        """
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def execute(self):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input and current event.
        """
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def finalise(self):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input.
        """
        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

    def _prepare_input(self, state):
        """Prepares objects on the store before the execution of the state methods.
        N.B.: config might not have a state and/or input fields defined. In this
        case, the KeyError exception is caught and the function simply returns.
        """
        for o in self.config["dependency"][state]:
            self.store.get(o)

    def _initialise(self):

        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("initialise")

    def _execute(self):

        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("execute")

    def _finalise(self):

        self.store.put(self.name, enums.Pyrate.NONE, "TRAN")

        self._prepare_input("finalise")


# EOF
