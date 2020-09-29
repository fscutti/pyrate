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
        self.set_targets(self.w_targets)

    def write(self, name):
        """"""
        h = R.TH1F("ThisIsATestHist", "ThisIsATestHist", 100, 0, 100)
        h.Fill(30, 2)
        # self.store.get(name, "PERM")
        self.f.WriteObject(h, name)


# EOF
