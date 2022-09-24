""" ROOT Output
"""

import ROOT
from ROOT import TFile
from pyrate.core.Algorithm import Algorithm

class OutputROOT(Algorithm):
    __slots__ = ["file", "directory", "path", "is_loaded", "targets"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.load()

    def load(self):
        """Creates the file and set targets.
        """
        self.is_loaded = True
        self.directory = self.config["path"]
        self.path = self.directory + "/" + self.name + ".root"
        self.targets = self.config["targets"]

        self.file = TFile(self.path, "RECREATE", self.name)

        # Set the file compression
        # compression = 1 if "compression" not in self.config else int(self.config["compression"])
        self.file.SetCompressionAlgorithm(ROOT.kLZ4)
        self.file.SetCompressionLevel(3)

        for t in self.targets:
            self.store.put(f"OUTPUT:{t}", self.file)
    
    def offload(self):
        self.is_loaded = False
        self.file.Close()
        del self.file

# EOF