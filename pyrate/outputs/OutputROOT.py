""" ROOT Output
"""

from pyrate.core.Algorithm import Algorithm

class OutputROOT(Algorithm):
    __slots__ = ["file", "directory", "path", "is_loaded", "targets"]

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)
        self.load()

    def load(self):
        """Creates the file and set targets.
        """
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        self.is_loaded = True
        self.directory = self.config["path"]
        self.path = self.directory + "/" + self.name + ".root"
        self.targets = self.config["targets"]

        self.file = ROOT.TFile(self.path, "RECREATE", self.name)

        # Set the file compression
        # compression = 1 if "compression" not in self.config else int(self.config["compression"])
        self.file.SetCompressionAlgorithm(ROOT.kLZ4)
        self.file.SetCompressionLevel(3)

        for t in self.targets:
            self.store.save(f"OUTPUT:{t}", self.file, save_copy=False)
    
    def offload(self):
        self.is_loaded = False
        self.file.Close()

# EOF