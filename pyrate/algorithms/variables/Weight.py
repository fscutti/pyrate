""" Computes a weight.
"""
import os
from copy import copy

from pyrate.core.Algorithm import Algorithm

class Weight(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        # Always avoid the top-level 'import ROOT'.
        import ROOT
        weight = 1

        if "value" in self.config:
            # This is the weight
            # https://www.youtube.com/watch?v=23n1qN-C6oE
            weight = self.config["value"]

        elif "applycalib" in self.config:

            h_calib = None

            if not self.store.check(self.config["applycalib"]["histname"], "PERM"):
                # if calibration histogram is not on the PERM store, need to open
                # a calibration file, retrieve the histogram, and put it on the store.
                # Note that this is an operation on the PERM store, so it will be
                # executed only one time throughout the Run, even if this is the execute
                # method of the Algorithm.
                file_calib = ROOT.TFile.Open(
                    os.path.join(
                        self.config["applycalib"]["filepath"],
                        self.config["applycalib"]["filename"],
                    )
                )

                # WARNING: we need to copy the histogram, as, when the file goes out of scope,
                # the histogram will be deleted by ROOT!!!
                h_calib = copy(file_calib.Get(self.config["applycalib"]["histname"]))

                self.store.put(self.config["applycalib"]["histname"], h_calib, "PERM")
                h_new = self.store.get(self.config["applycalib"]["histname"], "PERM")

            else:
                # if the calibration histogram already exist just retrieve it.
                h_calib = self.store.get(self.config["applycalib"]["histname"], "PERM")

            # the calibration to choose will depend on the value of another variable
            # which we will retrieve from the TRAN store.
            bin_value = self.store.get(self.config["applycalib"]["variable"]) / 10000
            bin_idx = h_calib.FindBin(bin_value)

            # This is the weight
            # https://www.youtube.com/watch?v=23n1qN-C6oE
            weight = h_calib.GetBinContent(bin_idx)

        self.store.put(self.name, weight)


# EOF
