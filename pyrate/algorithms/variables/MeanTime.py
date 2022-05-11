""" Find the mean time of the waveform in a given window region
    Mean time is calculated using 1/(sample_rate) * sum(A_i * t_i)/sum(A_i)

    Required parameters:
        rate: (float) The sample rate of the digitiser
        
        waveform: The waveform used to calculate the mean time
        window: The window object (tuple) for the calculation region
    
    Required states:
        initialise:
            output:
        execute:
            input: <Waveform object>, <Window object>
    
    Example config:

    MeanTime_CHX:
        algorithm:
            name: MeanTime
            rate: 500e6
        initialise:
            input:
        execute:
            input: CorrectedWaveform_CHX, Window_CHX
        waveform: CorrectedWaveform_CHX
        window: Window_CHX
"""

import numpy as np
from pyrate.core.Algorithm import Algorithm
from pyrate.utils.enums import Pyrate


class MeanTime(Algorithm):
    __slots__ = ("sample_period", "range")

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def initialise(self):
        """Gets the sample rate for later use in execute"""
        self.sample_period = 1 / float(self.config["algorithm"]["rate"])*1e9
        self.range = np.arange(0)

    def execute(self):
        waveform = self.store.get(self.config["waveform"])
        window = self.store.get(self.config["window"])

        # Check for valid values
        if waveform is Pyrate.NONE or window is Pyrate.NONE:
            self.store.put(self.name, Pyrate.NONE)
            return

        window_range = waveform[window[0]:window[1]].size # Number of indexes to sum over, just in case it goes over the end
        assert(window_range>=0)
        if self.range.size < window_range:
            # Need to resize the range
            self.range = np.arange(window_range)
        # Sum(waveform[i] * i)/ Sum()
        weighted_waveform = np.multiply(waveform[window[0]:window[1]], self.range[:window_range])
        num = np.sum(weighted_waveform)
        denom = np.sum(waveform[window[0]:window[1]])

        if denom == 0:
            # Can't divide by zero
            MeanTime = float("inf") # FIX ME
        else:
            MeanTime = self.sample_period * (num / denom)

        self.store.put(self.name, MeanTime)

# EOF

