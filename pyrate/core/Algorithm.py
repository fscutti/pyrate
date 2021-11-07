""" Algorithm class.
"""

"""
*************************************************************
config['name'] is the name of the object you want to compute.
*************************************************************
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


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
        pass

    def execute(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input and current event.
        """
        pass

    def finalise(self, config):
        """Override this method to define algorithms. config is a dictionary.
        The method is launched independently of the input or event.
        """
        pass

    def _prepare_input(self, config, state):
        """Prepares objects on the store before the execution of the state methods.
        N.B.: config might not have a state and/or input fields defined. In this
        case, the KeyError exception is caught and the function simply returns.
        """
        try:
            objs = ST.get_items_fast(config[state]["input"])

        except KeyError:
            return

        for o in objs:
            self.store.get(o)

    def _check_output(self, config, state):
        """This function checks that the required output has been put on the store."""
        try:
            objs = ST.get_items_fast(config[state]["output"])

        except KeyError:
            return True

        for o in objs:

            o = o.replace("SELF", config["name"])

            if not self.store.check(o):
                return False

        return True

    def _initialise(self, config):
        self._prepare_input(config, "initialise")

    def _execute(self, config):
        self._prepare_input(config, "execute")

    def _finalise(self, config):
        self._prepare_input(config, "finalise")


# EOF
