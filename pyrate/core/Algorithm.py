""" Algorithm class.
"""

"""
*************************************************************
config['name'] is the name of the object you want to compute.
*************************************************************
"""


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


# EOF
