""" Algorithm class.
"""


class Algorithm:
    __slots__ = ["name", "store"]

    def __init__(self, name, store):
        self.name = name
        self.store = store

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
