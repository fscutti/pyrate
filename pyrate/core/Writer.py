""" Generic Writer base class.
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = ["name", "store", "logger", "_targets", "_objects", "_is_loaded"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self._objects = {}
        self._targets = {}

    def load(self):
        """Initialises the targets. Also puts the writer
        in a state where something can be written on file (implies opening at least some files).
        """
        pass

    def write(self, name):
        """Write object to file. Will open the file if not already open."""
        pass

    def get_objects(self):
        """Returns objects."""
        return self._objects

    def get_targets(self):
        """Returns objects."""
        return self._targets

    def set_objects(self, objects):
        """Add targets from a list of objects."""
        for obj in objects:
            self._objects = FN.merge(self._objects, obj, merge_list=True)

    def set_targets(self):
        """Rearranges the target attribute."""
        for o, samples in self._objects.items():
            for s in samples:

                element = {"config": o.split(":", 1)[0], "name": o}

                if not s in self._targets:
                    self._targets[s] = [element]
                else:
                    self._targets[s].append(element)


# EOF
