""" Fill ROOT histograms. 
"""

import ROOT as R

from pyrate.core.Algorithm import Algorithm


class FillHists(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        # print("This is FillHists: ",self._store.objects)
        histogram = R.TH1F("TestHist", "TestHist", 10, 0, 10)
        self.store.put("filledHists", histogram, "PERM")
        # print("This is FillHists: ",self._store.objects)

    def execute(self, config):
        print("This is the MakePlot algorithm")

    def finalise(self, config):
        print("This is the MakePlot finalise method")
