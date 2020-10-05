""" Generic Writer base class.
"""
import ROOT as R
from pyrate.core.Writer import Writer


class WriterROOT(Writer):
    __slots__ = ["f", "w_target_list"]

    def __init__(self, name, store, logger, f, w_target_list):
        super().__init__(name, store, logger)
        self.f = f
        self.w_target_list = w_target_list

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
        self.add_targets(self.w_target_list)
        self.set_targets()

    def write(self, name):
        """"""
        h = R.TH1F("ThisIsATestHist", "ThisIsATestHist", 100, 0, 100)
        h.Fill(30, 2)
        # self.store.get(name, "PERM")
        self.f.WriteObject(h, name)


# EOF
