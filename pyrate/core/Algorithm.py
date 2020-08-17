""" Algorithm class.
"""

class Algorithm:
    def __init__(self):
        self._is_done = False
        self.store = {}

    def execute(self, edict):
        """ Override this method to define algorithms.
            edict is a dictionary.
        """
        pass

    def conditions(self):
        return self._is_done

    def stop(self):
        self._is_done = True


