""" Calculates a sum over a region of a waveform
    Sums the waveform over a passed in window object. 

    Required inputs:
        waveform: The waveform to caluclate the sum of (typically physcial)
        window: (tuple) The start and stop window for summing over
    
    Example config:
    
    Sum_CHX:
        algorithm: Sum
        input:
            waveform: CorrectedWaveform_CHX
            window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate

class Sum(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):
        """Sum over the waveform"""
        window = self.store.get(self.config["input"]["window"])
        waveform = self.store.get(self.config["input"]["waveform"])

        # check for invalid windows
        if window is Pyrate.NONE or waveform is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        # Sum the waveform
        Sum = np.sum(waveform[window[0] : window[1]])
        self.store.put(self.name, Sum)


# EOF
