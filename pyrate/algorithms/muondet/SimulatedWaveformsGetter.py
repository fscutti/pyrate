""" Get waveform of specific PMT.
"""
import sys
from copy import copy

import numpy as np

from pyrate.core.Algorithm import Algorithm


class SimulatedWaveformsGetter(Algorithm):
    __slots__ = ()

    def __init__(self, name, store, logger):
        super().__init__(name, store, logger)

    def execute(self, config):

        waveform = {"energy": [], "time": []}

        wf_map = self.store.get(config["waveform_map"])

        if config["pmt_name"] in wf_map:
            waveform = wf_map[config["pmt_name"]]

        self.store.put(config["name"], waveform)


# EOF
