""" Fill ROOT histograms. 
"""

from pyrate.core.Algorithm import Algorithm


class FillHists(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        # print("This is FillHists: ",self._store.objects)
        histogram = ROOT.TH1F("TestHist", "TestHist", 10, 0, 10)
        self.store.put("filledHists", histogram, "PERM")
        # print("This is FillHists: ",self._store.objects)

    def execute(self):
        print("This is the MakePlot algorithm")

    def finalise(self):
        print("This is the MakePlot finalise method")
