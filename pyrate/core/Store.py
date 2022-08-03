""" Store class.
The store is cleaned after every event/input iteration.
"""

import sys
from copy import copy

from pyrate.utils import enums as EN


class Store:
    def __init__(self, name):
        self.name = name
        self._transient = {}
        self._permanent = {}
        self._written = set()

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
            return EN.Pyrate.NONE

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

    def status(self, name, is_written=None):
        """Returns status of an object."""
        if is_written is not None:

            if is_written:
                self._written.add(name)

        else:
            if name in self._written:
                return EN.Pyrate.WRITTEN

            else:
                return EN.Pyrate.NONE


# EOF
