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
    __slots__ = ["name", "store", "logger"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger

    def initialise(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input.
        """
        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

    def execute(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input and current event.
        """
        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

    def finalise(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input.
        """
        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

    def _prepare_input(self, config, state):
        """Prepares objects on the store before the execution of the state methods.
        N.B.: config might not have a state and/or input fields defined. In this
        case, the KeyError exception is caught and the function simply returns.
        """
        for o in config["dependency"][state]:
            self.store.get(o)

    """
    def _check_output(self, config, state):
        #This function checks that the required output has been put on the store.
        try:
            objs = ST.get_items_fast(config[state]["output"])

        except KeyError:
            return True

        for o in objs:

            o = o.replace("SELF", config["name"])

            if not self.store.check(o):
                return False

        return True
    """

    def _initialise(self, config):

        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

        self._prepare_input(config, "initialise")

    def _execute(self, config):

        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

        self._prepare_input(config, "execute")

    def _finalise(self, config):

        self.store.put(config["name"], enums.Pyrate.NONE, "TRAN")

        self._prepare_input(config, "finalise")


# EOF
