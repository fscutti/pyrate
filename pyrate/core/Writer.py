""" Generic Writer base class.
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = ["name", "store", "logger", "targets", "_is_loaded"]

    def __init__(self, name, store, logger, targets={}):
        self.name = name
        self.store = store
        self.logger = logger
        self.targets = targets

    # def is_loaded(self):
    #    """Returns loading status of the Writer"""
    #    return self._is_loaded

    # def is_finished(self):
    #    """All objects have been written."""
    #    pass

    def load(self):
        """Initialises the targets. Also puts the writer
        in a state where something can be written on file (implies opening at least some files).
        """
        pass

    def write(self, name):
        """Write object to file. Will open the file if not already open."""
        pass

    def add_targets(self, objects):
        """Add targets from a list of objects."""
        for obj in objects:
            self.targets = FN.merge(self.targets, obj, merge_list=True)

    def set_targets(self):
        """Rearranges the target attribute."""
        new = {}

        for t, samples in self.targets.items():
            for s in samples:

                element = {"config": t.split(":", 1)[0], "name": t}

                if not s in new:
                    new[s] = [element]
                else:
                    new[s].append(element)

        self.targets = new


# EOF
