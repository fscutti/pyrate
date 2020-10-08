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
        # print("Calling: ", config["name"])

        raw_waveform = self.store.get(config["waveform"])

        # Need to create a copy as ROOT does not delete the object.

        hist_waveform = copy(R.TH1F(f"hist_waveform", f"hist_waveform", 100, 0, 100))
        for entry_idx, entry in enumerate(raw_waveform):
            hist_waveform.Fill(entry_idx, entry)

        self.store.put(config["name"], hist_waveform)


# EOF
