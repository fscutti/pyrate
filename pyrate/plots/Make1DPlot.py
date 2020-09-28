""" one-dimensional ROOT plot. 
"""

from pyrate.core.Algorithm import Algorithm


class Make1DPlot(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def initialise(self, config):
        # print("This is Make1DPlot: ", self.store.objects)
        # print(config["name"])
        # test = self.store.get(config["histograms"], "PERM")
        # test2 = self.store.get("PMT1_charge_waveform_muon","PERM")
        # test2.Print()

        # if test:
        #    test.Fill(5,1)
        #    self.store.put(config["name"], test, "PERM")
        #    print("The plot is ready")

        # print(self._store.objects)
        # for o,v in self.store.objects.items():
        #    v.Print("all")
        pass

    def execute(self, config):
        # self.store.get("energy")
        # print("This is the MakePlot algorithm")
        triggerTime = self.store.get("EVENT:SmallMuon:EventData:TriggerTime")
        print(triggerTime)

    def finalise(self, config):
        # print("This is the MakePlot finalise method")
        pass
