""" Uses physical waveform to calculate the baseline for the event. 
    Requires input from physical waveform and the number of samples used for the
    baseline calculation - this can be varied by the user and is defined in
    the config file.
    Takes the average of the first n samples in the waveform. Can be run on any
    waveform, typically PhysicalWaveform

    This can probably be improved to account for events/pulses at the start 
    of the event window.

    Required states:
        execute:
            input: <waveform>

    Required parameters:
        samples: The number of samples from the start to calculate the 
                 baseline over.
        waveform: The waveform object for which the baseline will be caluclated.
    
    Example config:

    Baseline_CHX:
        algorithm: 
            name: Baseline
            samples: 40
        execute:
            input: PhysicalWaveform_CHX
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
        method = self.config["method"]

        if method == "NP":
            # Get the baseline.
            Baseline, StdDev, Delta = self.BaselineNP(waveform, nsamples)

        elif method == "JITNP":
            # Get the baseline.
            Baseline, StdDev, Delta = self.BaselineJITNP(waveform, nsamples)

        elif method == "PyJIT":
            # Get the baseline.
            Baseline, StdDev, Delta = self.BaselinePyJIT(waveform, nsamples)

        #BaselineReco = [Baseline, StdDev, Delta]

        self.store.put(f"{self.name}", Baseline)
        self.store.put(f"{self.config['StdDev']}", StdDev)
        self.store.put(f"{self.config['Delta']}", Delta)

    @staticmethod
    def BaselineNP(waveform, nsamples):
        
        Baseline = np.sum(waveform[:nsamples]) / nsamples

        StdDev = np.std(waveform[:nsamples])

        Delta = np.max(waveform[:nsamples]) - np.min(waveform[:nsamples])

        return Baseline, StdDev, Delta

    @staticmethod
    @numba.jit(nopython=True, cache=True)
    def BaselineJITNP(waveform, nsamples):
        Baseline = -999.0
        StdDev = -999.0
        Delta = -999.0

        Baseline = np.sum(waveform[:nsamples]) / nsamples

        StdDev = np.std(waveform[:nsamples])

        Delta = np.max(waveform[:nsamples]) - np.min(waveform[:nsamples])

        return Baseline, StdDev, Delta

    @staticmethod
    @numba.jit(nopython=True, cache=True)
    def BaselinePyJIT(waveform, nsamples):
        Baseline = -999.0
        StdDev = 0.0
        Min = 999999.0
        Max = -999999.0
        Delta = -999.0
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

