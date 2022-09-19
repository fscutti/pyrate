""" Uses physical waveform to calculate the baseline for the event. 
    Requires input from physical waveform and the number of samples used for the
    baseline calculation - this can be varied by the user and is defined in
    the config file.
    Takes the average of the first n samples in the waveform. Can be run on any
    waveform, typically PhysicalWaveform

    This can probably be improved to account for events/pulses at the start 
    of the event window.

    Required parameters:
        samples: The number of samples from the start to calculate the 
                 baseline over.
    
    Required inputs:
        waveform: The waveform object for which the baseline will be caluclated.
    
    Example config:

    Baseline_CHX:
        algorithm: BaselineReco
        samples: 40
        input:
            waveform: PhysicalWaveform_CHX

    Todo: Get baseline automatically for ZLE firmware

"""
import numpy as np
import numba
from pyrate.core.Algorithm import Algorithm
import sys


class BaselineReco(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self):
        """Calculates the baseline from the first n samples of the waveform"""
        waveform = self.store.get(self.config["waveform"])

        if "samples" not in self.config["algorithm"]:
            sys.exit("ERROR in Baseline, 'samples' not found in the config")

        nsamples = self.config["samples"]
        
        Baseline, StdDev, Delta = self.BaselineCalc(waveform, nsamples)

        #BaselineReco = [Baseline, StdDev, Delta]

        self.store.put(f"{self.name}", Baseline)
        self.store.put(f"{self.config['StdDev']}", StdDev)
        self.store.put(f"{self.config['Delta']}", Delta)

    @staticmethod
    @numba.njit(cache=True)
    def BaselineCalc(waveform, nsamples):
        Baseline = Pyrate.NONE
        StdDev = 0.0
        Min = waveform[0]
        Max = waveform[0]
        Delta = Pyrate.NONE
        Sum = 0.0

        for i in range(nsamples):
            sample = waveform[i]
            Sum += sample
            StdDev += sample * sample
            if sample < Min:
                Min = sample
            if sample > Max:
                Max = sample

        Baseline = Sum / nsamples
        StdDev = np.sqrt(StdDev / nsamples - Baseline * Baseline)
        Delta = Max - Min

        return Baseline, StdDev, Delta





# EOF

