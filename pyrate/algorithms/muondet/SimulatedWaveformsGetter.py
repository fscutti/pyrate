""" Get waveform of specific PMT.
"""
import sys
from copy import copy

import numpy as np

from pyrate.core.Algorithm import Algorithm


class SimulatedWaveformsGetter(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):

        waveform = {"energy": [], "time": []}

        wf_map = self.store.get(self.config["input"]["waveform_map"])

        if self.config["pmt_name"] in wf_map:
            waveform = wf_map[self.config["pmt_name"]]

        self.store.put(self.name, waveform)


# EOF
