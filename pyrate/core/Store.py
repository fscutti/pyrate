""" Store class.
The store is cleaned after every event/input iteration.
"""

import sys
from copy import copy

from pyrate.utils import enums


class Store:
    def __init__(self, name):
        self.name = name
        self._store = {}

    def put(self, name, obj, replace=True):
        """Objects should be put on the store only once!"""
        if replace:
            self._store[name] = obj

    def get(self, name):
        """Get an object."""
        try:
            return self._store[name]

        except KeyError:
            return enums.Pyrate.NONE

    def copy(self, name):
        """Returns a copy of the object."""
        return copy(self.get(name))

    def clear(self):
        """Clears the store or portions of it."""
        self._store[l].clear()

# EOF
