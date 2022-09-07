""" Generic Writer base class.
"""
import sys
import ROOT as R
from pyrate.core.Writer import Writer

from pyrate.utils import enums as EN


class WriterROOT(Writer):
    __slots__ = ["f", "path"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def load(self):
        """Creates the file and set targets."""

        self.is_loaded = True

        self.path = self.config["path"]
        self.file = self.path + "/" + self.name + ".root"
        self.targets = self.config["targets"]

        self.f = R.TFile(self.file, "RECREATE")

        # Set the file compression
        compression = 1 if "compression" not in self.config else int(self.config["compression"])
        self.f.SetCompressionSettings(compression)

        # WARNING: if the file pointer needs to be retrieved from the store
        # by accessing the OUTPUT keys like follows, then is better for the
        # target to belong to just one output file.
        for t in self.targets:
            self.store.put(f"OUTPUT:{t}", self.f)

    def write(self, name):
        """Write an object to file. This can be represented by a structure
        indicating the folder structure of the output yet to be created at
        this point.
        """
        obj = self.store.get(name)

        if obj is EN.Pyrate.NONE:
            msg = f"ERROR: Cannot write the object '{name}' to file as it as not been saved to the store."
            sys.exit(msg)
            self.logger.error(msg)

        if isinstance(obj, dict):
            self._write_dirs(obj)
        else:
            self.f.WriteObject(obj, obj.GetName())

    def _write_dirs(self, obj):
        """Write dictionary of objects to file. The keys are the paths."""
        for path, item in obj.items():

            self._make_dirs(path)

            if isinstance(item, list):
                for i in item:
                    self.f.GetDirectory(path).WriteObject(i, i.GetName())
            else:
                self.f.GetDirectory(path).WriteObject(item, item.GetName())

    def _make_dirs(self, path):
        """Creates the path required to write an object."""
        if not self.f.GetDirectory(path):
            self.f.mkdir(path)


# EOF
