""" Generic Writer base class.
"""
import ROOT as R
from pyrate.core.Writer import Writer


class WriterROOT(Writer):
    __slots__ = ["f", "w_targets"]

    def __init__(self, name, store, logger, f, w_targets):
        super().__init__(name, store, logger)
        self.f = f
        self.w_targets = w_targets

    def load(self):
        """Creates the file and set targets."""
        self.is_loaded = True

        self.set_inputs_vs_targets(self.w_targets)
     
        self.f = R.TFile(self.f, "RECREATE")
        
        # WARNING: if the file pointer needs to be retrieved from the store
        # by accessing the OUTPUT keys like follows, then is better for the 
        # target to belong to just one output file.
        for t in self.get_targets():
            self.store.put(f"OUTPUT:{t}", self.f, "PERM")

    def write(self, name):
        """Write an object to file. This can be represented by a structure
        indicating the folder structure of the output yet to be created at
        this point.
        """
        obj = self.store.copy(name, "PERM")

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
