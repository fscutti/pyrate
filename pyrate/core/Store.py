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

    def put(self, name, obj, copy=False):
        """Objects should be put on the store only once!"""
        if not copy:
            self._store[name] = obj
        else:
            self._store[name] = copy(obj)

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

    def save(self, name):
        try:
            self._saved[name] = copy(self._store[name])

        except KeyError:
            sys.exit(
                f"ERROR: trying to save {name} but the object is not on the store."
            )

    def collect(self, name):
        """Get a saved object."""
        try:
            return self._saved[name]

        except KeyError:
            return enums.Pyrate.NONE


# EOF
