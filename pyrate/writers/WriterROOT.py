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

    # def is_loaded(self):
    #    """ Returns loading status of the Writer
    #    """
    #    return self._is_loaded

    # def is_finished(self):
    #    """
    #    """
    #    pass

    def load(self):
        """"""
        self.f = R.TFile(self.f, "RECREATE")
        self.set_objects(self.w_objects)
        self.set_targets()

    def write(self, name):
        """"""
        obj = self.store.get(name, "PERM")

        if isinstance(obj, dict):
            self._write_dirs(obj)

        # self.f.WriteObject(h, name)

    def _write_dirs(self, obj, path="/"):
        for k, v in obj.items():
            self.f.cd(path)
            self.f.mkdir(k)
            directory = path + k + "/"
            self.f.cd(directory)
            # if isinstance(v, dict):
            #    self._write_dirs(v, path=directory)
            # else:
            #    self.f.WriteObject(v, directory+v.GetName())
            self.f.WriteObject(v, directory + v.GetName())


# EOF
