""" Algorithm class.
"""

class Algorithm:
    __slots__ = ("_is_done", "store")
    def __init__(self):
        self._is_done = False
        self.store = {}

    def execute(self, config):
        """ Override this method to define algorithms.
            config is a dictionary.
        """
        pass

    def conditions(self):
        return self._is_done

    def stop(self):
        self._is_done = True


