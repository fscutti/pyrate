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
        self._saved = {}

    def put(self, name, obj):
        """Puts an object on the store."""
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
        """Clears the store."""
        self._store.clear()

    def save(self, name, obj, save_copy=True):
        """Saves an object for later collection."""
        if save_copy:
            self._saved[name] = copy(obj)
        else:
            self._saved[name] = obj

    def collect(self, name):
        """Get a saved object."""
        try:
            return self._saved[name]

        except KeyError:
            return enums.Pyrate.NONE


# EOF
