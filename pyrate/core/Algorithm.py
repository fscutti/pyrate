""" Algorithm class.
"""

class Algorithm:
    __slots__ = ["name", "store", "_is_done"]
    def __init__(self, name, store):
        self.name = name
        self.store = store
        self._is_done = False

    def execute(self, config = None):
        """ Override this method to define algorithms.
            config is a dictionary.
        """
        pass

    def conditions(self):
        return self._is_done

    def stop(self):
        self._is_done = True


