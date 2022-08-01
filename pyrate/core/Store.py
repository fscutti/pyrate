""" Store class.
The store is cleaned after every event/input iteration.
"""

import sys
from copy import copy

from pyrate.utils import enums


class Store:
    def __init__(self, name):
        self.name = name
        self._transient = {}
        self._permanent = {}

    def put(self, name, obj):
        """Puts an object on the store."""
        self._transient[name] = obj

    def get(self, name):
        """Get an object."""
        try:
            return self._transient[name]

        except KeyError:
            pass

        try:
            return self._permanent[name]

        except KeyError:
            return enums.Pyrate.NONE

    def copy(self, name):
        """Returns a copy of the object."""
        return copy(self.get(name))

    def clear(self):
        """Clears the store."""
        self._transient.clear()

    def save(self, name, obj, save_copy=True):
        """Saves an object for later collection."""
        if save_copy:
            self._permanent[name] = copy(obj)
        else:
            self._permanent[name] = obj


# EOF
