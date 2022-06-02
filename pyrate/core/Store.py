""" Store class.
PERM:
    objects which are persistent throughout the run.
TRAN:
    objects which are volatile and removed after each input/event loop.
"""

import sys
from copy import copy
import traceback

from pyrate.utils import functions as FN
from pyrate.utils import enums


class Store:
    def __init__(self, name):
        self.name = name
        self.state = None
        self._objects = {"PERM": {}, "TRAN": {}}
        self._default = {"initialise": "PERM", "execute": "TRAN", "finalise": "PERM"}

    def put(self, name, obj, location=None, replace=False):
        """Objects should be put on the store only once!"""

        if location is None:

            if self.state is None:
                location = "TRAN"

            else:
                location = self._default[self.state]

        if self.check(name, location) and not replace:
            """To do: handle warning at this stage."""
            return

        self._objects[location][name] = obj

    def get(self, name, location=["TRAN", "PERM"]):
        """try/except among objects."""

        if isinstance(location, list):
            for l in location:
                if name in self._objects[l]:
                    return self._objects[l][name]

        else:
            return self._objects[location][name]

        return enums.Pyrate.NONE

    def copy(self, name, location=["TRAN", "PERM"]):
        """Returns a copy of the object."""
        return copy(self.get(name, location))

    def check(self, name, location=["TRAN" "PERM"]):
        """Checks if object is in the store."""

        if isinstance(location, str):
            return name in self._objects[location]

        else:
            return any([name in self._objects[l] for l in location])

    def clear(self, location=["TRAN", "PERM"]):
        """Clears the store or portions of it."""

        if isinstance(location, str):
            self._objects[location].clear()

        else:
            for l in location:
                self._objects[l].clear()


# EOF
