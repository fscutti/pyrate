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
        self._store[l].clear()

    def save(self, name, replace=False, copy=True):
        """Saves an object for later collection."""
        if not name in self._store:
            sys.exit(
                f"ERROR: trying to save {name} but the object is not on the store."
            )
        if not replace and name in self._saved:
            sys.exit(f"ERROR: trying to save {name} but the object is already saved.")

        if copy:
            self._saved[name] = copy(self._store[name])
        else:
            self._saved[name] = self._store[name]

    def collect(self, name):
        """Get a saved object."""
        try:
            return self._saved[name]

        except KeyError:
            return enums.Pyrate.NONE


# EOF
