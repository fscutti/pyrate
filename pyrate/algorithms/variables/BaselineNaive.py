""" Uses physical waveform to calculate the baseline for the event. 
    Requires input from physical waveform and the number of samples used for the
    baseline calculation - this can be varied by the user and is defined in
    the config file.

    Takes the average of the first n samples in the waveform. Can be run on any
    waveform, typically PhysicalWaveform. Does not check for any pulses in said window.

    Baseline is an improvement to account for events/pulses at the start 
    of the event window, but is slower and so using this alg may still be preferable.

    Required parameters:
        samples: The number of samples from the start to calculate the 
                 baseline over.
    
    Required inputs:
        waveform: The waveform object for which the baseline will be caluclated.
    
    Example config:

    Baseline_CHX:
        algorithm: BaselineNaive
        samples: 40
        input:
            waveform: PhysicalWaveform_CHX

    Todo: Get baseline automatically for ZLE firmware

"""
import sys
import numpy as np
from pyrate.core.Algorithm import Algorithm
import sys
from scipy.ndimage.filters import uniform_filter1d
from pyrate.utils.enums import Pyrate
import numba


class BaselineNaive(Algorithm):
    __slots__ = ()

    def __init__(self, name, config, store, logger):
        super().__init__(name, config, store, logger)

    def execute(self, condition=None):
        """Calculates the baseline from the first n samples of the waveform"""
        waveform = self.store.get(self.config["input"]["waveform"])

        if "samples" not in self.config:
            sys.exit("ERROR in Baseline, 'samples' not found in the config")

        nsamples = self.config["samples"]

        if waveform is Pyrate.NONE or waveform.size < nsamples:
            return

        # Get the baseline from the front of the waveform.
        Baseline = self.BaselineCalc(waveform=waveform, nsamples=nsamples)

        self.store.put(self.name, Baseline)

    @staticmethod
    @numba.njit(cache=True)
    def BaselineCalc(waveform, nsamples):
        
        Sum = 0.0
        Baseline = Pyrate.NONE
        
        # Get the baseline from the front of the waveform.
        for i in range(nsamples):
            Sum += waveform[i]
        
        Baseline = Sum / nsamples

        return Baseline


# EOF

