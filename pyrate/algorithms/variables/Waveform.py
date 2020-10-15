""" Executes basic operations on raw waveform.
"""

from pyrate.core.Algorithm import Algorithm
from copy import copy

import ROOT as R


class Waveform(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):
        raw_waveform = self.store.get(config["waveform"])

        # Need to create a copy as ROOT does not delete the object.
        # The risk of not copying is to have multiple instances of the
        # histogram if the algorithm is run on the same event to make
        # different objects.
        nbins = len(raw_waveform)
        hist_waveform = copy(
            R.TH1F(f"hist_waveform", f"hist_waveform", nbins, 0, nbins)
        )

        for time_idx, adc in enumerate(raw_waveform):
            hist_waveform.Fill(time_idx, adc)

        self.store.put(config["name"], hist_waveform)


# EOF
