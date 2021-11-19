""" Generic Writer base class.
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = ["name", "store", "logger", "is_loaded", "_inputs_vs_targets", "_targets"]

    def __init__(self, name, store, logger):
        self.name = name
        self.store = store
        self.logger = logger
        self.is_loaded = False
        self._targets = {}
        self._inputs_vs_targets = {}

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

    def get_inputs_vs_targets(self):
        """Returns objects."""
        return self._inputs_vs_targets

    def set_inputs_vs_targets(self, targets):
        """Rearranges the target attribute."""

        for t in targets:
            self._targets = FN.merge(self._targets, t, merge_list=True)

        for t, inputs in self._targets.items():
            for i in inputs:

                element = {"name": t, "object": t.split(":", 1)[0]}

                if not i in self._inputs_vs_targets:
                    self._inputs_vs_targets[i] = [element]
                else:
                    self._inputs_vs_targets[i].append(element)


# EOF
