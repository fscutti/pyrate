""" Generic Writer base class.
"""
from pyrate.utils import strings as ST
from pyrate.utils import functions as FN


class Writer:
    __slots__ = [
        "name",
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
        self._targets = None
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
    def file(self, path):
        """Setter method for targets."""

        if len(self.name.split(".")) == 1:
            sys.exit(f"ERROR: format not declared for writer {self.name}")

        else:
            self._file = os.path.join(path, self.name)

    @property
    def targets(self):
        """Getter method for targets."""
        return self._targets

    @targets.setter
    def targets(self, config):
        """Setter method for targets."""
        for t in config:

            t_name = t.replace(" ", "")
            t_inputs = ST.get_items(t.split(":")[1])

            self._targets[t_name] = t_inputs


# EOF
