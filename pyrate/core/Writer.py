""" Generic Writer base class.
"""
import os

from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = [
        "name",
        "config",
        "store",
        "logger",
        "is_loaded",
        "_targets",
        "_file",
    ]

    def __init__(self, name, config, store, logger):
        self.name = name
        self.config = config
        self.store = store
        self.logger = logger

        self.is_loaded = False

        self._targets = {}
        self._file = None

    def load(self):
        """Initialises the targets."""
        pass

    def write(self, name):
        """Write object to file. Will open the file if not already open."""
        pass

    @property
    def file(self):
        """Getter method for targets."""
        return self._file

    @file.setter
    def file(self, file_path):
        """Setter method for targets."""
        if self._file is None:
            self._file = file_path

    @property
    def targets(self):
        """Getter method for targets."""
        return self._targets

    @targets.setter
    def targets(self, target_list):
        """Setter method for targets."""
        if not any(self._targets):

            for t in target_list:

                for t_name, t_inputs in t.items():
                    t_name = t_name.replace(" ", "")
                    self._targets[t_name] = t_inputs


# EOF
