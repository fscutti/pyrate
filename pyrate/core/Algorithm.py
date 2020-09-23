""" Algorithm class.
"""


class Algorithm:
    __slots__ = ["name", "store", "logger"]

    def __init__(self, name, store):
        self.name = name
        self.store = store
        self.logger = logger

    def initialise(self, config):
        """Override this method to define algorithms.
        config is a dictionary.
        """
        pass

    def execute(self, config):
        """Override this method to define algorithms.
        config is a dictionary.
        """
        pass

    def finalise(self, config):
        """Override this method to define algorithms.
        config is a dictionary.
        """
        pass


# EOF
