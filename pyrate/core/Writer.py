""" Generic Writer base class.
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = ["name", "store", "logger", "_config_targets", "_targets", "_is_loaded"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self._targets = {}
        self._config_targets = {}

    def load(self):
        """Initialises the targets. Also puts the writer
        in a state where something can be written on file (implies opening at least some files).
        """
        pass

    def write(self, name):
        """Write object to file. Will open the file if not already open."""
        pass

    def get_targets(self):
        """Returns objects."""
        return self._targets

    def get_config_targets(self):
        """Returns objects."""
        return self._config_targets

    def set_targets(self, targets):
        """Add targets from a list of objects."""
        for t in targets:
            self._targets = FN.merge(self._targets, t, merge_list=True)

    def set_config_targets(self):
        """Rearranges the target attribute."""
        for t, samples in self._targets.items():
            for s in samples:

                element = {"config": t.split(":", 1)[0], "name": t}

                if not s in self._config_targets:
                    self._config_targets[s] = [element]
                else:
                    self._config_targets[s].append(element)


# EOF
