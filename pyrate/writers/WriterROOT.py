""" Generic Writer base class.
"""
import ROOT as R
from pyrate.core.Writer import Writer


class WriterROOT(Writer):
    __slots__ = ["f", "w_objects"]

    def __init__(self, name, store, logger, f, w_objects):
        super().__init__(name, store, logger)
        self.f = f
        self.w_objects = w_objects

    def load(self):
        """Creates the file and set targets."""
        self.f = R.TFile(self.f, "RECREATE")
        self.set_objects(self.w_objects)
        self.set_targets()

    def write(self, name):
        """Write an object to file. This can be represented by a structure
        indicating the folder structure of the output yet to be created at 
        this point.
        """
        obj = self.store.get(name, "PERM")

        if isinstance(obj, dict):
            self._write_dirs(obj)
        else:
            self.f.WriteObject(obj, obj.GetName())

    def _write_dirs(self, obj):
        """Write dictionary of objects to file. The keys are the paths."""
        for entry, o in obj.items():

            path = entry.rsplit("/", 1)[0]

            self._make_dirs(path)
            self.f.GetDirectory(path).WriteObject(o, o.GetName())

    def _make_dirs(self, path):
        """Creates the path required to write an object."""
        if not self.f.GetDirectory(path):
            self.f.mkdir(path)


# EOF
