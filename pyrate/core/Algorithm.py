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
        self.store.put(config["name"], "PYRATE:none", "PERM")

    def execute(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input and current event.
        """
        self.store.put(config["name"], "PYRATE:none", "TRAN")

    def finalise(self, config):
        """Override this method to define algorithms. config is a dictionary.
        At this stage the method knows the current input.
        """
        self.store.put(config["name"], "PYRATE:none", "PERM")

    def _prepare_input(self, config, state):
        """Prepares objects on the store before the execution of the state methods.
        N.B.: config might not have a state and/or input fields defined. In this
        case, the KeyError exception is caught and the function simply returns.
        """
        if state == "initialise":
            all_states = ["initialise", "execute", "finalise"]
            for s in all_states:
                for o in config["dependency"][s]:
                    self.store.get(o)
        else:
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

        self.store.put(config["name"], "PYRATE:none", "PERM")

        self._prepare_input(config, "initialise")

    def _execute(self, config):

        self.store.put(config["name"], "PYRATE:none", "TRAN")

        self._prepare_input(config, "execute")

    def _finalise(self, config):

        self.store.put(config["name"], "PYRATE:none", "PERM")

        self._prepare_input(config, "finalise")


# EOF
